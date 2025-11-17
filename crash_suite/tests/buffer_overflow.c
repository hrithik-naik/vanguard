#include <stdio.h>
#include <string.h>

int main() {
    printf("[buffer_overflow] Triggering stack buffer overflow...\n");
    char buf[8];
    strcpy(buf, "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");
    return 0;
}
