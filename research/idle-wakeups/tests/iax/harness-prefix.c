#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <poll.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/time.h>
#include <sys/timerfd.h>
#include <time.h>
#include <unistd.h>

struct ast_sockaddr { int value; };
struct ast_timer { int fd; };
struct iax2_trunk_peer {
    pthread_mutex_t lock;
    int sockfd;
    struct ast_sockaddr addr;
    struct timeval trunkact;
    unsigned int lastsent;
    unsigned int trunkdatalen;
    unsigned int trunkdataalloc;
    unsigned char *trunkdata;
    int calls;
    struct { struct iax2_trunk_peer *next; } list;
};
static struct {
    struct iax2_trunk_peer *first, *last;
    pthread_mutex_t lock;
} tpeers = {.lock = PTHREAD_MUTEX_INITIALIZER};
static _Thread_local int list_locked;
#define AST_LIST_LOCK(h) do { assert(!list_locked); assert(!pthread_mutex_lock(&(h)->lock)); list_locked = 1; } while (0)
#define AST_LIST_UNLOCK(h) do { assert(list_locked); list_locked = 0; assert(!pthread_mutex_unlock(&(h)->lock)); } while (0)
#define AST_LIST_EMPTY(h) (!(h)->first)
#define AST_LIST_TRAVERSE(h, v, f) for ((v) = (h)->first; (v); (v) = (v)->f.next)
#define AST_LIST_INSERT_TAIL(h, v, f) do { if ((h)->last) (h)->last->f.next=(v); else (h)->first=(v); (h)->last=(v); } while (0)
#define AST_LIST_TRAVERSE_SAFE_BEGIN(h, v, f) { __typeof__(h) _head=(h); struct iax2_trunk_peer *_prev=NULL, *_next, *_current; for ((v)=(h)->first; (v); _prev=_current,(v)=_next) { _next=(v)->f.next; _current=(v);
#define AST_LIST_REMOVE_CURRENT(f) do { if (_prev) _prev->f.next=_next; else _head->first=_next; if (!_next) _head->last=_prev; _current=_prev; } while (0)
#define AST_LIST_TRAVERSE_SAFE_END } }

#define ast_mutex_init(m) pthread_mutex_init((m), NULL)
#define ast_mutex_lock(m) pthread_mutex_lock(m)
#define ast_mutex_unlock(m) pthread_mutex_unlock(m)
#define ast_mutex_destroy(m) pthread_mutex_destroy(m)
#define ast_calloc calloc
#define ast_free free
#define LOG_WARNING 1
#define LOG_ERROR 2
#define LOG_NOTICE 3
static int warning_count, error_count, setter_calls, sent_frames;
static int fail_rate = -1;
static int fail_count;
static int iaxtrunkdebug, trunkmaxsize = 128000, trunk_timed;
static int trunkfreq = 20;
static struct ast_timer timer_storage;
static struct ast_timer *timer = &timer_storage;
static unsigned int trunk_timer_rate;
static int trunk_timer_idle_disabled;
static int trunk_timer_error_logged;

static void ast_log(int level, const char *format, ...)
{
    (void)format;
    if (level == LOG_WARNING) ++warning_count;
    if (level == LOG_ERROR) ++error_count;
}
static void ast_debug(int level, const char *format, ...) { (void)level; (void)format; }
static void ast_verbose(const char *format, ...) { (void)format; }
static struct timeval ast_tvnow(void) { struct timeval tv; assert(!gettimeofday(&tv, NULL)); return tv; }
static int ast_sockaddr_cmp(const struct ast_sockaddr *a, const struct ast_sockaddr *b) { return a->value != b->value; }
static void ast_sockaddr_copy(struct ast_sockaddr *a, const struct ast_sockaddr *b) { *a = *b; }
static const char *ast_sockaddr_stringify(const struct ast_sockaddr *a) { (void)a; return "test-peer"; }
static int ast_timer_set_rate(const struct ast_timer *t, unsigned int rate)
{
    struct itimerspec spec = {0};
    assert(list_locked);
    ++setter_calls;
    if ((int)rate == fail_rate && fail_count) { --fail_count; errno = EIO; return -1; }
    if (rate) spec.it_value.tv_nsec = spec.it_interval.tv_nsec = 1000000000L / rate;
    return timerfd_settime(t->fd, 0, &spec, NULL);
}
static int ast_timer_ack(const struct ast_timer *t, unsigned int quantity)
{
    uint64_t ticks;
    ssize_t bytes;
    (void)quantity;
    bytes = read(t->fd, &ticks, sizeof(ticks));
    return bytes == sizeof(ticks) || (bytes < 0 && errno == EAGAIN) ? 0 : -1;
}
static int send_trunk(struct iax2_trunk_peer *peer, struct timeval *now)
{
    int calls = peer->calls;
    if (peer->trunkdatalen) {
        ++sent_frames;
        peer->trunkact = *now;
        peer->trunkdatalen = 0;
        peer->calls = 0;
    }
    return calls;
}
