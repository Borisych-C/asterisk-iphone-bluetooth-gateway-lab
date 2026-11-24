
static int ready(int timeout_ms)
{
    struct pollfd pfd = {.fd = timer->fd, .events = POLLIN};
    return poll(&pfd, 1, timeout_ms);
}
static double monotonic_ms(void)
{
    struct timespec ts;
    assert(!clock_gettime(CLOCK_MONOTONIC, &ts));
    return ts.tv_sec * 1000.0 + ts.tv_nsec / 1e6;
}
static void setup(void)
{
    assert(AST_LIST_EMPTY(&tpeers));
    timer->fd = timerfd_create(CLOCK_MONOTONIC, TFD_NONBLOCK | TFD_CLOEXEC);
    assert(timer->fd >= 0);
    trunk_timer_rate = trunk_timer_idle_disabled = trunk_timer_error_logged = 0;
    trunkfreq = 20;
    setter_calls = warning_count = error_count = sent_frames = 0;
    fail_rate = -1;
    fail_count = 0;
}
static void expire_all(void)
{
    struct iax2_trunk_peer *peer;
    AST_LIST_LOCK(&tpeers);
    AST_LIST_TRAVERSE(&tpeers, peer, list) {
        ast_mutex_lock(&peer->lock);
        peer->trunkact.tv_sec = 0;
        ast_mutex_unlock(&peer->lock);
    }
    AST_LIST_UNLOCK(&tpeers);
}
static void teardown(void)
{
    fail_rate = -1;
    expire_all();
    while (!AST_LIST_EMPTY(&tpeers)) assert(timing_read(NULL, timer->fd, POLLIN, NULL) == 1);
    assert(!close(timer->fd));
}
static struct iax2_trunk_peer *get_peer(int id)
{
    struct ast_sockaddr address = {.value = id};
    return find_tpeer(&address, -1);
}
static void invariant(void)
{
    struct itimerspec spec;
    AST_LIST_LOCK(&tpeers);
    assert(!timerfd_gettime(timer->fd, &spec));
    if (AST_LIST_EMPTY(&tpeers) && !trunk_timer_idle_disabled) {
        assert(trunk_timer_rate == 0);
        assert(spec.it_interval.tv_nsec == 0);
    } else {
        assert(trunk_timer_rate == 1000U / (unsigned int)trunkfreq);
        assert(spec.it_interval.tv_nsec == 1000000000L / trunk_timer_rate);
    }
    AST_LIST_UNLOCK(&tpeers);
}
static void basic_and_reload(void)
{
    struct iax2_trunk_peer *peer, *same;
    double start, first_tick;
    int calls;
    setup();
    assert(ready(70) == 0);
    apply_trunkfreq(20);
    assert(setter_calls == 0 && ready(70) == 0);
    start = monotonic_ms();
    peer = get_peer(1);
    assert(peer);
    peer->trunkdatalen = 160;
    peer->calls = 1;
    ast_mutex_unlock(&peer->lock);
    assert(trunk_timer_rate == 50);
    calls = setter_calls;
    usleep(8000);
    same = get_peer(1);
    assert(same == peer);
    ast_mutex_unlock(&same->lock);
    assert(setter_calls == calls); /* A frame must not postpone the pending flush. */
    assert(ready(70) == 1);
    first_tick = monotonic_ms() - start;
    assert(first_tick < 90.0);
    assert(timing_read(NULL, timer->fd, POLLIN, NULL) == 1);
    assert(sent_frames == 1 && peer->trunkdatalen == 0);
    apply_trunkfreq(40);
    assert(trunkfreq == 40 && trunk_timer_rate == 25);
    fail_rate = 10;
    fail_count = 1;
    apply_trunkfreq(100);
    assert(trunkfreq == 40 && trunk_timer_rate == 25); /* Failed reload preserves effective period. */
    fail_rate = -1;
    expire_all();
    assert(timing_read(NULL, timer->fd, POLLIN, NULL) == 1);
    invariant();
    assert(ready(70) == 0);
    assert(timing_read(NULL, timer->fd, POLLIN, NULL) == 1); /* Stale callback stays registered. */
    apply_trunkfreq(20);
    assert(trunkfreq == 20 && trunk_timer_rate == 0 && ready(70) == 0);
    peer = get_peer(2);
    assert(peer && trunk_timer_rate == 50);
    ast_mutex_unlock(&peer->lock);
    assert(ready(70) == 1);
    teardown();
    printf("PASS idle, first frame flush, existing peer no rearm, reload active/idle/failure, stale callback (first tick %.3f ms)\n", first_tick);
}
static void errors(void)
{
    struct iax2_trunk_peer *peer;
    int calls;
    setup();
    fail_rate = 50;
    fail_count = 2;
    assert(get_peer(3) == NULL);
    assert(get_peer(3) == NULL);
    assert(AST_LIST_EMPTY(&tpeers) && error_count == 1 && trunk_timer_rate == 0);
    peer = get_peer(3);
    assert(peer && trunk_timer_rate == 50 && trunk_timer_error_logged == 0);
    ast_mutex_unlock(&peer->lock);
    fail_rate = 0;
    fail_count = 1;
    expire_all();
    assert(timing_read(NULL, timer->fd, POLLIN, NULL) == 1);
    assert(AST_LIST_EMPTY(&tpeers) && trunk_timer_idle_disabled && warning_count == 1);
    calls = setter_calls;
    for (int i = 0; i < 20; ++i) assert(timing_read(NULL, timer->fd, POLLIN, NULL) == 1);
    assert(setter_calls == calls && warning_count == 1); /* No disarm retries or log storm. */
    invariant();
    assert(ready(70) == 1); /* The previous functional periodic fallback is retained. */
    peer = get_peer(4);
    assert(peer);
    peer->trunkdatalen = 160;
    peer->calls = 1;
    ast_mutex_unlock(&peer->lock);
    assert(timing_read(NULL, timer->fd, POLLIN, NULL) == 1);
    assert(sent_frames == 1);
    teardown();
    puts("PASS arm failure does not accept peer; recovery; disarm failure retains periodic timing without retry/log storm");
}
static pthread_barrier_t phase;
static void *peer_producer(void *unused)
{
    (void)unused;
    for (int i = 0; i < 1000; ++i) {
        struct iax2_trunk_peer *peer;
        pthread_barrier_wait(&phase);
        peer = get_peer(i + 100);
        assert(peer);
        peer->trunkact.tv_sec = 0; /* Allow cleanup in the concurrent pass. */
        ast_mutex_unlock(&peer->lock);
        pthread_barrier_wait(&phase);
        pthread_barrier_wait(&phase);
    }
    return NULL;
}
static void race_first_peer_and_cleanup(void)
{
    pthread_t producer;
    setup();
    assert(!pthread_barrier_init(&phase, NULL, 2));
    assert(!pthread_create(&producer, NULL, peer_producer, NULL));
    for (int i = 0; i < 1000; ++i) {
        pthread_barrier_wait(&phase);
        assert(timing_read(NULL, timer->fd, POLLIN, NULL) == 1);
        pthread_barrier_wait(&phase);
        invariant(); /* No lost arm after a concurrent last-peer cleanup. */
        pthread_barrier_wait(&phase);
    }
    assert(!pthread_join(producer, NULL));
    assert(!pthread_barrier_destroy(&phase));
    teardown();
    puts("PASS 1000 concurrent first-peer creation / idle cleanup interleavings; timer always agrees with runtime list");
}
int main(void)
{
    basic_and_reload();
    errors();
    race_first_peer_and_cleanup();
    puts("All extracted-function timerfd tests passed; protocol integration and target ABI are separate checks.");
    return 0;
}
