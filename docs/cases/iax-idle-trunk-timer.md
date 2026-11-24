# IAX2 schedules 50 timer wakeups per second with no active trunks

Case `iax-idle-trunk-timer` · **confirmed-reproduced**

## Diagnosis

At the default 20 ms trunk frequency the periodic timer remains armed when there are no runtime trunk peers.

## Resolution

Start the timer under the peer list lock when the first peer is created. Stop it when cleanup removes the last peer, and update the active rate on reload.

## Evidence and limits

On the tested 20.6.0 package the idle network thread went from 49.99 to 1.00 voluntary context switches per second. A Linux timerfd harness covered failures and 1,000 creation/cleanup races. Earlier protocol checks used two isolated instances of the actual module.

[Evidence and reproduction](../../research/idle-wakeups/README.md) · [Patch](../../research/idle-wakeups/0002-iax-demand-trunk-timer.patch).

## Reports

[Asterisk #2338](https://github.com/asterisk/asterisk/issues/2338).
