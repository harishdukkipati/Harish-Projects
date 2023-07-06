// Asgn 2: A simple HTTP server.
// By: Eugene Chou
//     Andrew Quinn
//     Brian Zhao
//
#include "asgn2_helper_funcs.h"
#include "connection.h"
#include "debug.h"
#include "response.h"
#include "request.h"
#include "queue.h"

#include <pthread.h>
#include <err.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>

#include <sys/file.h>
#include <sys/stat.h>

queue_t *q = NULL;

void audit(char *req, char *uri, int status_code, char *id);

void handle_connection(int);

int worker_threads();
//void *dispatcher_thread(void *);

void handle_get(conn_t *);
void handle_put(conn_t *);
void handle_unsupported(conn_t *);
pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
//pthread_mutex_t file = PTHREAD_MUTEX_INITIALIZER;
//pthread mutex_t cond = PTHREAD_COND_INITIALIZER

int main(int argc, char **argv) {
    if (argc < 2) {
        warnx("wrong arguments: %s port_num", argv[0]);
        fprintf(stderr, "usage: %s <port>\n", argv[0]);
        return EXIT_FAILURE;
    }

    int num_threads = 4;
    int opt = 0;

    while ((opt = getopt(argc, argv, "t: ")) != -1) {
        switch (opt) {
        case 't':
            num_threads = atoi(optarg);
            break;
            //default: num_threads = 4; break;
        }
    }

    //printf("%d\n", num_threads);

    char *endptr = NULL;
    size_t port = (size_t) strtoull(argv[argc - 1], &endptr, 10);
    if (endptr && *endptr != '\0') {
        warnx("invalid port number: %s", argv[argc - 1]);
        return EXIT_FAILURE;
    }

    signal(SIGPIPE, SIG_IGN);
    Listener_Socket sock;
    listener_init(&sock, port);

    q = queue_new(num_threads);

    pthread_t worker_t[num_threads];
    for (int i = 0; i < num_threads; i++) {
        pthread_create(&worker_t[i], NULL, (void *(*) (void *) ) worker_threads, NULL);
    }

    while (1) {
        //fprintf(stderr, "monkey");
        uintptr_t connfd = listener_accept(&sock);
        //void* c = &connfd;
        if (!queue_push(q, (void *) connfd)) {
            fprintf(stderr, "Internal server error");
            return EXIT_FAILURE;
        }
        //fprintf(stderr, "%lu", connfd);
        //handle_connection(connfd);
        //close(connfd);
    }

    return EXIT_SUCCESS;
}

int worker_threads() {
    uintptr_t confd;
    while (1) {
        if (!queue_pop(q, (void **) &confd)) {
            fprintf(stderr, "Internal server error");
            return EXIT_FAILURE;
        }
        handle_connection(confd);
        close(confd);
    }
    return 0;
}

void handle_connection(int connfd) {

    conn_t *conn = conn_new(connfd);

    const Response_t *res = conn_parse(conn);

    if (res != NULL) {
        conn_send_response(conn, res);
    } else {
        //debug("%s", conn_str(conn));
        const Request_t *req = conn_get_request(conn);
        if (req == &REQUEST_GET) {
            handle_get(conn);
        } else if (req == &REQUEST_PUT) {
            handle_put(conn);
        } else {
            handle_unsupported(conn);
        }
    }

    conn_delete(&conn);
}

void handle_get(conn_t *conn) {
    //pthread_mutex_t lock = PTHREAD_MUTEX_INITIALIZER;
    char *request = "GET";
    char *uri = conn_get_uri(conn);
    char *rid = NULL;
    rid = conn_get_header(conn, "Request-Id");
    //char *header = conn_get_header(conn, NULL);
    //fprintf(stderr, "%s", header);
    //const Response_t *res = NULL;
    //debug("GET request not implemented. But, we want to get %s", uri);

    //bool existed = access(uri, F_OK) == 0;
    //debug("%s existed? %d", uri, existed);
    pthread_mutex_lock(&lock);

    int fd = open(uri, O_RDONLY, 0666);
    //ftruncate(fd, 1);

    //pthread_mutex_unlock(&lock);
    //flock(fd, LOCK_SH);
    if (fd < 0) {
        //debug("%s: %d", uri, errno);
        if (errno == EACCES) {
            conn_send_response(conn, &RESPONSE_FORBIDDEN);
            audit(request, uri, 403, rid);
            //close(fd);
            //return;
        } else if (errno == ENOENT) {
            conn_send_response(conn, &RESPONSE_NOT_FOUND);
            audit(request, uri, 404, rid);
            //close(fd);
            //return;
        } else {
            conn_send_response(conn, &RESPONSE_INTERNAL_SERVER_ERROR);
            audit(request, uri, 500, rid);
            //close(fd);
            //return;
        }
        pthread_mutex_unlock(&lock);
        close(fd);
        return;
    }

    struct stat check;
    stat(uri, &check);

    if (S_ISDIR(check.st_mode)) {
        conn_send_response(conn, &RESPONSE_FORBIDDEN);
        audit(request, uri, 403, rid);
        pthread_mutex_unlock(&lock);
        close(fd);
        return;
    }

    pthread_mutex_unlock(&lock);

    flock(fd, LOCK_SH); //LOCK_SH because you can have multiple readers

    struct stat st;
    fstat(fd, &st);

    int content_length = 0;
    content_length = st.st_size;

    //ftruncate(fd, content_length);

    //bool existed = access(uri, F_OK) == 0;

    conn_send_file(conn, fd, content_length);
    audit(request, uri, 200, rid);

    //flock(fd, LOCK_UN);

    //if (res == NULL && existed) {
    //	res = &RESPONSE_OK;
    //}

    //flock(fd, LOCK_UN);

    close(fd); //close fd automatically unlocks the flock
}

void audit(char *req, char *uri, int status_code, char *id) {
    fprintf(stderr, "%s,/%s,%d,%s\n", req, uri, status_code, id);
}

void handle_unsupported(conn_t *conn) {
    debug("handling unsupported request");

    // send responses
    conn_send_response(conn, &RESPONSE_NOT_IMPLEMENTED);
}

void handle_put(conn_t *conn) {
    //pthread_mutex_t file = PTHREAD_MUTEX_INITIALIZER;
    //pthread_cond_t cond;
    char *request = "PUT";
    char *uri = conn_get_uri(conn);
    const Response_t *res = NULL;
    char *rid = NULL;
    rid = conn_get_header(conn, "Request-Id");
    //debug("handling put request for %s", uri);
    pthread_mutex_lock(&lock); //lock file creation

    // Check if file already exists before opening it.
    bool existed = access(uri, F_OK) == 0;
    //pthread_mutex_lock(&file);
    //if (!existed) {
    //	int fd = open(uri, O_WRONLY | O_TRUNC, 0600);
    //}
    //pthread_mutex_lock(&file);
    //while(access(uri, F_OK) != -1) {
    //      existed = 0;
    //	    pthread_cond_wait(&cond, &file);
    //}
    //debug("%s existed? %d", uri, existed);

    //int status = 0;

    // Open the file..
    int fd = open(uri, O_CREAT | O_WRONLY, 0600);
    flock(fd, LOCK_EX); //use LOCK_EX so only one thread can access lock
    ftruncate(fd, 1);
    //pthread_mutex_unlock(&file); //unlock file creation

    int status = 0;
    if (fd < 0) {
        //debug("%s: %d", uri, errno);
        if (errno == EACCES || errno == EISDIR || errno == ENOENT) {
            res = &RESPONSE_FORBIDDEN;
            status = 403;
            goto out;
            //audit(request, uri, 403, rid);
        } else {
            res = &RESPONSE_INTERNAL_SERVER_ERROR;
            status = 500;
            goto out;
            //audit(request, uri, 500, rid);
        }
    }

    //ftruncate(fd, 1);
    //flock(fd, LOCK_EX);
    pthread_mutex_unlock(&lock);
    //flock(fd, LOCK_EX);
    res = conn_recv_file(conn, fd);
    //flock(fd, LOCK_UN);

    if (res == NULL && existed) {
        res = &RESPONSE_OK;
        status = 200;
        goto out;
        //audit(request, uri, 200, rid);
    } else if (res == NULL && !existed) {
        res = &RESPONSE_CREATED;
        status = 201;
        goto out;
        //audit(request, uri, 201, rid);
    }

    //flock(fd, LOCK_UN);

    //flock(fd, LOCK_UN);

    //close(fd);

out:
    audit(request, uri, status, rid);
    conn_send_response(conn, res);
    close(fd);
    //pthread_mutex_unlock(&file);
}
