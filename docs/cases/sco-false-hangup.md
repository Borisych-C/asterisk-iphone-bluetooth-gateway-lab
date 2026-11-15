# Call disconnects immediately on answer

Case: `sco-false-hangup` · Evidence: **confirmed-reproduced**

Search terms: chan_mobile NULL frame, partial read, EAGAIN, ECONNRESET, iPhone SCO replacement

## Diagnosis

The old read path could return NULL after a partial frame or transient SCO failure. NULL means channel termination, not temporarily missing audio. The iPhone also replaced SCO around answer.

## Resolution

Keep call lifecycle separate from audio socket lifecycle; return ast_null_frame, discard incomplete buffers on disconnect and accept the replacement socket.

## Evidence and limits

Model tests cover partial frames, EAGAIN/EINTR, EOF, reset and reconnect. Real calls survived replacement. Cause of every kernel Bluetooth warning was not established.

## Code and reproduction

- [Implementation](../../recovery/2026-11-14/work/chan_mobile.c)
- [Test or detailed evidence](../../recovery/2026-11-14/work/test.c)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
