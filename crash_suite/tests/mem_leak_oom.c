#include <stdlib.h>
#include <stdio.h>

int main() {
    printf("[use_after_free] Triggering use-after-free...\n");
    int *p = malloc(sizeof(int));
    free(p);
    *p = 42;
    return 0;
}
