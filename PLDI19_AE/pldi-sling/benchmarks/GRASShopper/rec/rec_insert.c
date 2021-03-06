#include "header.h"
#include <stdlib.h>
#include <stdio.h>

Node * rec_insert(Node * lst, Node * elt)
{
  //pre
  if (lst == NULL) {
      //post
    return elt;
  } else {
    int nondet = rand()%3 - 1;
    if (nondet) {
      elt->next = lst;
      //post
      return elt;
    } else {
      Node * n1 = lst->next;
      Node * n2 = rec_insert(n1, elt);
      lst->next = n2;
      //post
      return lst;
    }
  }
}

int main(int argc, char * argv[]){
    int size = 0;
    sscanf(argv[1],"%d",&size);
    Node * lst = create_list(size);
    Node * elt = (Node *)malloc(sizeof(Node));
    elt->next = NULL;
    Node * res = rec_insert(lst, elt);
    rec_insert(NULL, elt);
    return 0;
}
