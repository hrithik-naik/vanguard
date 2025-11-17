#include <pthread.h>
#include <stdio.h>

int shared = 0;

void* worker(void* arg) {
    for (int i = 0; i < 100000000; i++)
        shared++; // race condition
    return NULL;
}

int main() {
    printf("[race_condition] Triggering data race...\n");

    pthread_t t1, t2;
    pthread_create(&t1, NULL, worker, NULL);
    pthread_create(&t2, NULL, worker, NULL);

    pthread_join(t1, NULL);
    pthread_join(t2, NULL);

    printf("[race_condition] Done — shared value=%d\n", shared);
    return 0;
}
