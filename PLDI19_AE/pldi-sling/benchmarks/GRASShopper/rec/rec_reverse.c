#include "header.h"
#include <stdlib.h>
#include <stdio.h>

Node * rec_reverse_acc(Node * curr, Node * rev);
Node * rec_reverse(Node * lst);

Node * rec_reverse_acc(Node * curr, Node * rev)
{
  //pre
  if (curr == NULL) {
    //post
    return rev;
  } else {
    Node * tmp = curr->next;
    curr->next = rev;
    Node * ret = rec_reverse_acc(tmp, curr);
    //post
    return ret;
  }
}

Node * rec_reverse(Node * lst)
{
  return rec_reverse_acc(lst, NULL);
}

int main(int argc, char * argv[]){
    int size = 0;
    sscanf(argv[1],"%d",&size);
    Node * lst = create_list(size);
    Node * res = rec_reverse(lst);
    rec_reverse(NULL);
    return 0;
}
