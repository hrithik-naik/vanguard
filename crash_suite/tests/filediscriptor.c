#include <fcntl.h>
#include <stdio.h>

int main() {
    printf("[fd_leak] Opening files forever...\n");
    while (1) open("/dev/null", O_RDONLY);
}
