#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include <bluetooth/bluetooth.h>
#include <bluetooth/sco.h>
#define CHANNEL_FRAME_SIZE 320
#define AST_FRIENDLY_OFFSET 64
#define AST_FRAME_VOICE 1
#define DEVICE_FRAME_FORMAT 1
#define MIN(a,b) ((a)<(b)?(a):(b))
#define ast_debug(...) ((void)0)
#define ast_log(...) ((void)0)
#define ast_mutex_trylock(...) 0
#define ast_mutex_unlock(...) ((void)0)
#define CHANNEL_DEADLOCK_AVOIDANCE(...) ((void)0)
#define ast_channel_set_fd(...) ((void)0)
struct ast_frame {
    int frametype, datalen, samples, offset, mallocd;
    struct { int format; } subclass;
    const char *src;
    struct { long tv_sec, tv_usec; } delivery;
    union { void *ptr; } data;
};
static struct ast_frame ast_null_frame;
struct ast_smoother {
    unsigned size, used;
    unsigned char data[4096], output[320];
    struct ast_frame frame;
};
static void ast_smoother_reset(struct ast_smoother *s, unsigned n)
{ assert(n && n <= 320); s->size=n; s->used=0; }
static void ast_smoother_feed(struct ast_smoother *s, const struct ast_frame *f)
{ assert(s->used+f->datalen<=sizeof(s->data)); memcpy(s->data+s->used,f->data.ptr,f->datalen); s->used+=f->datalen; }
static struct ast_frame *ast_smoother_read(struct ast_smoother *s)
{
    if (s->used<s->size) return NULL;
    memcpy(s->output,s->data,s->size);
    s->used-=s->size;
    memmove(s->data,s->data+s->size,s->used);
    s->frame.data.ptr=s->output; s->frame.datalen=s->size;
    return &s->frame;
}
struct mbl_pvt {
    void *owner;
    struct ast_frame fr;
    int lock, sco_socket, do_alignment_detection, dsp;
    uint16_t sco_mtu, sco_tx_size;
    char id[32], io_buf[CHANNEL_FRAME_SIZE+AST_FRIENDLY_OFFSET];
    struct ast_smoother *bt_in_smoother, *bt_out_smoother;
};
struct ast_channel { struct mbl_pvt *pvt; };
#define ast_channel_tech_pvt(c) ((c)->pvt)
static void do_alignment_detection(struct mbl_pvt *p, void *b, int n) { (void)p; (void)b; (void)n; }
static struct ast_frame *ast_dsp_process(struct ast_channel *c, int d, struct ast_frame *f) { (void)c; (void)d; return f; }
static int option_error;
static int test_getsockopt(int fd, int level, int option, void *p, socklen_t *n)
{
    (void)fd; assert(level==SOL_SCO && option==SCO_OPTIONS);
    if (option_error) return -1;
    assert(*n==sizeof(struct sco_options));
    ((struct sco_options *)p)->mtu=255;
    return 0;
}
#define getsockopt test_getsockopt
#include "host_framing.inc"
#include "audio_functions.inc"

int main(void)
{
    struct ast_smoother input={0}, output={0};
    struct mbl_pvt p={.owner=&p,.bt_in_smoother=&input,.bt_out_smoother=&output};
    struct ast_channel chan={.pvt=&p};
    int pair[2]; unsigned char bytes[320], got[320];
    for (unsigned i=0;i<sizeof(bytes);i++) bytes[i]=(unsigned char)i;
    struct ast_frame voice={.frametype=AST_FRAME_VOICE,.datalen=320,.samples=160,.data.ptr=bytes};
    assert(!socketpair(AF_UNIX,SOCK_SEQPACKET,0,pair)); p.sco_socket=pair[0];
    sco_configure_socket(&p);
    assert(p.sco_mtu==255 && p.sco_tx_size==0);
    mbl_write(&chan,&voice);
    assert(recv(pair[1],got,sizeof(got),MSG_DONTWAIT)==-1 && errno==EAGAIN);
    for (int i=0;i<7;i++) {
        assert(send(pair[1],bytes,48,0)==48);
        struct ast_frame *f=mbl_read(&chan);
        assert(f && (i==6 ? f->datalen==320 : f==&ast_null_frame));
    }
    assert(p.sco_tx_size==48);
    mbl_write(&chan,&voice);
    for(int i=0;i<6;i++) { assert(recv(pair[1],got,sizeof(got),MSG_DONTWAIT)==48); assert(!memcmp(got,bytes+i*48,48)); }
    assert(output.used==32);
    sco_observe_packet(&p,96);
    assert(p.sco_tx_size==96 && !output.used);
    mbl_write(&chan,&voice);
    for(int i=0;i<3;i++) { assert(recv(pair[1],got,sizeof(got),MSG_DONTWAIT)==96); assert(!memcmp(got,bytes+i*96,96)); }
    close(pair[1]);
    assert(mbl_read(&chan)==&ast_null_frame && p.sco_socket==-1 && p.sco_tx_size==0);
    assert(!socketpair(AF_UNIX,SOCK_SEQPACKET,0,pair)); p.sco_socket=pair[0];
    sco_configure_socket(&p);
    assert(!input.used && !output.used && !p.sco_tx_size);
    assert(send(pair[1],bytes,60,0)==60);
    assert(mbl_read(&chan)==&ast_null_frame && p.sco_tx_size==60);
    assert(mbl_read(&chan)==&ast_null_frame); /* Partial frame + EAGAIN is not hangup. */
    option_error=1; sco_configure_socket(&p);
    assert(!p.sco_mtu && !p.sco_tx_size);
    close(pair[0]); close(pair[1]);
    assert(sco_host_packet_size(60,255)==60);
    assert(sco_host_packet_size(120,255)==120);
    assert(sco_host_packet_size(48,31)==30);
    assert(!sco_host_packet_size(49,255));
    assert(!sco_host_packet_size(0,255));
    assert(!sco_host_packet_size(48,0));
    assert(!sco_host_packet_size(322,255));
    puts("PASS: real seqpacket read/write, dynamic 48/60/96/120, no premature TX, MTU bound, partial frame/EAGAIN, EOF/reconnect, no stale PCM");
}
