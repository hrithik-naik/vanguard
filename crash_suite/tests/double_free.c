#include <stdlib.h>
#include <stdio.h>

int main() {
    printf("[double_free] Triggering double free...\n");
    int *p = malloc(sizeof(int));
    free(p);
    free(p);
    return 0;
}
