#include <stdio.h>

int main(void) {
    printf("About to crash via NULL dereference...\n");
    fflush(stdout);

    int *p = NULL;
    *p = 1;  // deliberate crash

    return 0;
}
