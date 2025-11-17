#include <stdio.h>

int main() {
    printf("[null_deref] Triggering NULL pointer crash...\n");
    fflush(stdout);

    int *p = NULL;
    *p = 10;
    return 0;
}
