# Call disconnects immediately on answer

Case: `sco-false-hangup` · Evidence: **confirmed-reproduced**

Search terms: chan_mobile NULL frame, partial read, EAGAIN, ECONNRESET, iPhone SCO replacement

## Diagnosis

The old read path could return NULL after a partial frame or transient SCO failure. NULL means channel termination, not temporarily missing audio. The iPhone also replaced SCO around answer.

## Resolution

Keep call lifecycle separate from audio socket lifecycle; return ast_null_frame, discard incomplete buffers on disconnect and accept the replacement socket.

## Evidence and limits

A real 20.6.0 call survived SCO replacement with the local correction. With a nonblocking socket pair and a model smoother, the stock callback from 20.22.0, 22.12.0, 24.0.0 and master cfb0aa2a returned NULL after 48 bytes and EAGAIN. The corrected regression test covers EOF, reset and reconnect.

To repeat the stock failure on Linux, download the chosen upstream addons/chan_mobile.c and pass its path to [check-stock-sco-read.py](../../recovery/2026-11-14/work/check-stock-sco-read.py). The script prints the callback return, buffered byte count and errno. Exit 1 with frame=NULL reproduces the failure. The corrected test below verifies recovery.

## Code and reproduction

- [Implementation](../../recovery/2026-11-14/work/chan_mobile.c)
- [Test or detailed evidence](../../recovery/2026-11-14/work/test.c)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.

## Reports

[Asterisk #2336](https://github.com/asterisk/asterisk/issues/2336).
