#include <linux/bpf.h>
#include <sys/syscall.h>
#include <unistd.h>
#include <stdio.h>

int main() {
    struct bpf_insn prog[] = {{0}}; // invalid

    printf("[bpf] Loading malformed BPF program...\n");
    syscall(__NR_bpf, 0 /* BPF_PROG_LOAD */, prog, sizeof(prog));

    return 0;
}
