#define _GNU_SOURCE
#include <sys/prctl.h>
#include <linux/seccomp.h>
#include <unistd.h>
#include <stdio.h>

int main() {
    // Enable strict seccomp - only allows read/write/exit
    prctl(PR_SET_SECCOMP, SECCOMP_MODE_STRICT);

    // This syscall is NOT allowed → kernel logs and kills process
    syscall(39); // getpid()
    return 0;
}
