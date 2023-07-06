#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <stdbool.h>
#include <stdint.h>
#include <pthread.h>
#include "queue.h"

typedef struct queue {
    int size;
    int in;
    int out;
    int count;
    void **buffer;
    pthread_mutex_t lock;
    pthread_cond_t not_full;
    pthread_cond_t not_empty;
} queue_t;

queue_t *queue_new(int size) {
    queue_t *q = (queue_t *) malloc(sizeof(queue_t));
    if (q == NULL) {
        return NULL;
    }
    q->size = size;
    q->in = 0;
    q->out = 0;
    q->count = 0;
    q->buffer = (void **) malloc(size * sizeof(void *));
    if (q->buffer == NULL) {
        free(q);
        return NULL;
    }
    pthread_mutex_init(&q->lock, NULL);
    pthread_cond_init(&q->not_full, NULL);
    pthread_cond_init(&q->not_empty, NULL);
    return q;
}

bool queue_push(queue_t *q, void *elem) {
    pthread_mutex_lock(&q->lock);
    if (q == NULL) {
        return false;
    }
    while (q->count == q->size) {
        pthread_cond_wait(&q->not_full, &q->lock);
    }
    q->buffer[q->in] = elem;
    q->in = (q->in + 1) % q->size;
    q->count++;
    pthread_cond_signal(&q->not_empty);
    pthread_mutex_unlock(&q->lock);

    return true;
}

bool queue_pop(queue_t *q, void **elem) {
    pthread_mutex_lock(&q->lock);
    if (q == NULL) {
        return false;
    }
    while (q->count == 0) {
        pthread_cond_wait(&q->not_empty, &q->lock);
    }
    *elem = q->buffer[q->out];
    q->out = (q->out + 1) % q->size;
    q->count--;

    pthread_cond_signal(&q->not_full);
    pthread_mutex_unlock(&q->lock);

    return true;
}

void queue_delete(queue_t **q) {
    if (!q || !(*q)) {
        return;
    }

    if ((*q)->buffer) {
        free((*q)->buffer);
    }
    pthread_mutex_destroy(&(*q)->lock);
    pthread_cond_destroy(&(*q)->not_full);
    pthread_cond_destroy(&(*q)->not_empty);
    free(*q);
    *q = NULL;
}
