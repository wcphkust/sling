#include "header.h"
#include <stdlib.h>
#include <stdio.h>

void g_list_free(DLNode * list)
{
  DLNode * pos = list;
  while(pos != NULL){
      printf("%d\n", pos->key);
      pos = pos->next;
  }
  printf("--\n");
  //pre
  DLNode * x = list;
  DLNode * next = NULL;
  while(x != NULL)
  {
    //loop
    next = x->next;
    free(x);
    x = next;
  }
  //free(list);
  //while(list != NULL){
  if(list != NULL){
      printf("%d\n", list->key);
      list = list->next;
  }
//  }
  //post
}

int main(int argc, char * argv[]){
    int size = 0;
    sscanf(argv[1],"%d", &size);
    DLNode * hd = create_list(size);
    g_list_free(hd);
    return 0;
}
