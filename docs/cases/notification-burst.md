# Seven service messages appear at once after one SMS

Case: `notification-burst` · Evidence: **confirmed-sender-only**

Search terms: Linphone push notification batching queued check status spam

## Diagnosis

Server recorded four checks, one old rejection and two success-path statuses at different times. User saw seven together. One cellular request existed; batching location was not identified.

## Resolution

Do not send diagnostic or queued notifications to the user chat. Keep one phone-acceptance notice and explicit errors. Record diagnostic results in logs.

## Evidence and limits

Do not claim seven SMS sends, or blame a particular client/server queue without evidence. A quiet check verified no new chat message.

## Code and reproduction

- [Implementation](../../sms-bridge/outgoing.py)
- [Test or detailed evidence](../../SMS-SEND.txt)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
