# Idle wakeups in chan_mobile and chan_iax2

On a Linux Mint 22.3 x86-64 host running the Ubuntu Noble Asterisk 20.6.0 package, two threads woke regularly with zero calls, no connected Bluetooth phone and no IAX2 trunk traffic. The two measurements below came from the same process. The baseline window was 60 s and the post-change window was 180 s.

| Thread | Before, voluntary context switches/s | After, voluntary context switches/s |
| --- | ---: | ---: |
| Bluetooth SCO listener | 981.34 | 1.00 |
| IAX2 network thread | 49.99 | 1.00 |

Together these changes reduced the service's CPU use from 1.5225% to 0.4786% of one core in those windows. The experiment measured their combined CPU effect.

## Bluetooth listener

With the phone disconnected, observe the SCO listener thread in a short syscall trace. In the stock module the socket accept context is polled with zero timeout, followed by a one-millisecond wait on an empty audio context. Established audio has its own channel descriptor. The measured thread repeated the pair approximately once per millisecond.

The [listener patch](0001-mobile-idle-wait.patch) waits for socket readiness with a one-second upper bound. A new connection immediately wakes the thread. The finite timeout bounds the race between checking for unload and entering the wait. The standalone Linux socket tests covered eight scenarios in both an optimized build and an AddressSanitizer/UndefinedBehaviorSanitizer build, including socket readiness, interruption and unload.

## IAX2 trunk timer

With chan_iax2 loaded, no runtime trunk peers and the default 20 ms trunk frequency, inspect the Asterisk process's timerfd metadata and the network thread's voluntary switches. The stock periodic timer stays armed at 50 Hz.

The [timer patch](0002-iax-demand-trunk-timer.patch) arms the timer when it creates the first runtime trunk peer and disarms it when the existing cleanup removes the last one. Both decisions use the trunk peer list lock. A configuration reload updates an active timer and leaves an idle one stopped. The lifecycle tests used a real Linux timerfd, including failed rate changes and 1,000 races between peer creation and cleanup. Earlier tests on two isolated instances of the actual 20.6.0 module included trunk media, ordinary calls, registration, qualify, DTMF, and module reload.

Both local harnesses passed again on 24 November 2026. Both diffs also passed a zero-fuzz application check on upstream tags 20.22.0, 22.12.0, 24.0.0 and master at cfb0aa2a. The on-host performance and protocol measurements above are from the 20.6.0 package. These diffs must be built for the target Asterisk ABI.

## Repeating the standalone tests

In a scratch directory, apply the corresponding diff to an Asterisk source checkout with `patch -p1`. Copy the [mobile harness directory](tests/mobile) or [IAX harness directory](tests/iax) to a scratch location. Put the patched `addons/chan_mobile.c` alongside `run-tests.py`, or the patched `channels/chan_iax2.c` alongside `run-harness.py`, respectively. Run the Python script with a C compiler and the Linux sanitizer runtime available. It extracts and compiles the relevant functions, runs both builds and writes the detailed outcomes in the scratch directory. No Bluetooth, trunk peer or running Asterisk service is needed for these harnesses.
