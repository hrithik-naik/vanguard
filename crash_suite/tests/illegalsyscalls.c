#define _GNU_SOURCE
#include <unistd.h>
#include <stdio.h>
#include <sys/syscall.h>

int main() {
    printf("[illegal_syscall] Triggering unknown syscall...\n");
    long result = syscall(9999); // Nonexistent syscall
    printf("Returned: %ld\n", result);
    return 0;
}
