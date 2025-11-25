#include <sys/mman.h>
#include <unistd.h>
int main() {
    char *p = mmap(NULL, getpagesize(), PROT_NONE, MAP_PRIVATE|MAP_ANONYMOUS, -1, 0);
    p[0] = 'A'; // illegal write
    return 0;
}
