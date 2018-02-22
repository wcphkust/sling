from seplogic import *
from trace import *
from printer import *
from debug import *
import z3
import operator

ops = {
    ArithOp.ADD: operator.add,
    ArithOp.SUB: operator.sub,
    ArithOp.MUL: operator.mul,
    ArithOp.DIV: operator.truediv,
    RelOp.LT: operator.lt,
    RelOp.LE: operator.le,
    RelOp.GT: operator.gt,
    RelOp.GE: operator.ge,
    RelOp.EQ: operator.eq,
    RelOp.NE: operator.ne }

class Store(object):
    def __init__(self):
        self.store = {}

    def __ho_str__(self, f):
        s = ''
        for v in self.store:
            s += str(v) + ' = ' + f(self.store[v]) + '\n'
        return s

    def __str__(self):
        return str(self.store)

    def add(self, v, val):
        self.store[v] = val

    def remove(self, v):
        if v in self.store:
            del self.store[v]

    def get(self, v):
        return self.store[v]

    def contains(self, v):
        return v in self.store

    def clone(self):
        copy = Store()
        copy.store = self.store.copy()
        return copy

    def update(self, another_store):
        self.store.update(another_store.store)

    def dom(self):
        return self.store.keys()

    def disjoint(self, another_store):
        return all(elem not in self.store
                   for elem in another_store.dom())

    def union(self, another_store):
        if self.disjoint(another_store):
            us = self.clone()
            us.update(another_store)
            return us
        else:
            raise Exception('Two stores are not disjoint')

    def eval(self, e, func='eval'):
        method_name = func + '_' + type(e).__name__
        if not hasattr(self, method_name):
            method_name = 'eval_' + type(e).__name__
        default_eval = lambda func: lambda e: self.generic_eval(e, func)
        evaluation = getattr(self, method_name, default_eval(func))
        if method_name.startswith('eval'):
            return evaluation(e, func)
        else:
            return evaluation(e)

    def generic_eval(self, e, func):
        raise Exception('No evaluation ' + '(' + func + ') ' +
                        'for ' + str(e) + ':' + type(e).__name__)

class Stack(Store):
    def __init__(self):
        Store.__init__(self)
        self.solver = z3.Solver()
        self.solver.set("timeout", 500)
        self.z3_symtab = {}

    def __str__(self):
        return self.__ho_str__(str)

    # Evaluation expressions to values
    def eval_Var(self, e, func='eval'):
        return self.get(e.id).val

    def eval_IConst(self, e, func='eval'):
        return e.val

    def eval_BinOp(self, e, func='eval'):
        el = self.eval(e.left, func)
        er = self.eval(e.right, func)
        return ops[e.op](el, er)

    def eval_BConst(self, e, func='eval'):
        return e.val

    def eval_PBinRel(self, e, func='eval'):
        el = self.eval(e.left, func)
        er = self.eval(e.right, func)
        return ops[e.op](el, er)

    # Translation to z3 formulas
    def trans_Var(self, e):
        try:
            return self.eval(e) # Return the stack value of e
        except:
             v = e.id
             if v in self.z3_symtab:
                 return self.z3_symtab[v]
             else:
                 zv = z3.Int(v)
                 self.z3_symtab[v] = zv
                 return zv

    def trans_PConj(self, e):
        el = self.eval(e.left, 'trans')
        er = self.eval(e.right, 'trans')
        return z3.And(el, er)

    def trans_PDisj(self, e):
        el = self.eval(e.left, 'trans')
        er = self.eval(e.right, 'trans')
        return z3.Or(el, er)

    def trans_PNeg(self, e):
        ev = self.eval(e.form, 'trans')
        return z3.Not(ev)

    def trans_PQuant(self, Quant, e):
        ne = e.rename()

        # Create z3's bounded variables
        zvs = []
        for v in ne.vars:
            vid = v.id
            if vid in self.z3_symtab:
                zvs.append(self.z3_symtab[vid])
            else:
                zv = z3.Int(vid)
                self.z3_symtab[vid] = zv
                zvs.append(zv)
        f = self.eval(ne.form, 'trans')
        if Quant == PExists:
            ef = z3.Exists(zvs, f)
        else:
            ef = z3.ForAll(zvs, f)
        return ef

    def trans_PExists(self, e):
        return self.trans_PQuant(PExists, e)

    def trans_PForall(self, e):
        return self.trans_PQuant(PForall, e)

    def evaluate(self, e):
        ef = self.eval(e, 'trans')
        debug(ef)
        self.solver.push()
        self.solver.add(ef)
        try:
            r = self.solver.check()
            if r == z3.unsat:
                return Ternary(False)
            elif r == z3.sat:
                # m = self.solver.model()
                return Ternary(True)
            else:
                return Ternary(None) # unknown
        except:
            return Ternary(None)
        finally:
            self.solver.pop()

class Heap(Store):
    def __str__(self):
        str_of_heap = (lambda (t, fs):
                       '(' + t + ')' + str_of_list(fs, str))
        return self.__ho_str__(str_of_heap)

class SHModel(object):
    def __init__(self, stack, heap):
        self.stack = stack
        self.heap = heap

    def satisfy(self, f):
        method_name = 'satisfy_' + type(f).__name__
        checker = getattr(self, method_name, self.generic_satisfy)
        return checker(f)

    def generic_satisfy(self, f):
        raise Exception('No model checker for ' +
                        str(f) + ':' + type(f).__name__)

    def satisfy_FBase(self, f):
        stk_eval = self.stack.evaluate(f.pure)
        if stk_eval == True:
            heap_eval = self.stack.evaluate(self.satisfy(f.heap))
            return heap_eval
        else:
            return stk_eval

    def satisfy_HEmp(self, f):
        dom_h = self.heap.dom()
        is_empty_dom = not(bool(dom_h))
        return BConst(is_empty_dom)

    def satisfy_HData(self, f):
        dom_h = self.heap.dom()
        if len(dom_h) == 1:
            s = self.stack
            h = self.heap
            root = s.eval(Var(f.root))
            addr = Addr(root)
            (typ, fields) = h.get(addr)
            if typ == f.name:
                field_vals = map(lambda f: f.data.val, fields)
                f_args = f.args
                match = map(lambda (a, v): PBinRel(a, '=', IConst(v)),
                            zip(f_args, field_vals))
                cond = reduce(lambda m1, m2: PConj(m1, m2), match)
                return cond
            else: # The sorts are inconsistent
                debug('HData: ' + f.root + ' points to inconsistent data types'
                      + '(' + typ + ', ' + f.name + ')')
                return BConst(False)
        else:
            debug ('HData: The heap domain contains more than one data nodes')
            return BConst(False)

    def satisfy_HStar(self, f):
        s = self.stack
        h = self.heap
        hdata_lst, hpred_lst = f.partition()
        debug(str_of_list(hdata_lst, str))
        debug(str_of_list(hpred_lst, str))
        explicit_hdata_lst = filter(lambda d: s.contains(d.root), hdata_lst)
        h2 = h.clone()
        for d in explicit_hdata_lst:
            try:
                # Matching explicit data nodes with the heap model
                root = s.eval(Var(d.root))
                h1 = Heap()
                h1.add(root, h2.get(root))
                m1 = SHModel(s, h1)
                c1 = m1.satisfy(d)
                debug(c1)
                h2.remove(root)
            except:
                debug('HStar: Cannot find the matched heap for HData')
                return BConst(False)
        debug(str_of_list(explicit_hdata_lst, str))
        return BConst(False)

