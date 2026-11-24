# Bluetooth SCO listener wakes about 1,000 times per second at idle

Case `mobile-idle-polling` · **confirmed-reproduced**

## Diagnosis

The listener polls the SCO accept context without waiting, then waits one millisecond on the empty audio I/O context.

## Resolution

Wait for socket readiness on the accept context with a one-second upper bound for unload.

## Evidence and limits

On the tested 20.6.0 package the idle thread went from 981.34 to 1.00 voluntary context switches per second. Eight standalone scenarios passed in optimized and sanitizer builds. The patch applies without fuzz to three later releases and master.

[Evidence and reproduction](../../research/idle-wakeups/README.md) · [Patch](../../research/idle-wakeups/0001-mobile-idle-wait.patch).

## Reports

[Asterisk #2337](https://github.com/asterisk/asterisk/issues/2337).
