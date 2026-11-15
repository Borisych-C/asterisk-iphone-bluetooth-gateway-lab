# PushMessage completes but recipient has no SMS

Case: `iphone-map-outgoing` · Evidence: **observed-device**

Search terms: iPhone MAP Uploading bMessage originator vCard green bubble Not Delivered SMS iMessage

## Diagnosis

MAP completion means phone acceptance, not carrier delivery. One accepted transfer produced Not Delivered; manual SMS retry succeeded. A later new message arrived automatically after delay.

## Resolution

Use UTF-8 bMessage with originator/recipient structure; distinguish queued, submitting, handed-to-phone and unknown. Never automatically repeat an ambiguous cellular send.

## Evidence and limits

An empty originator vCard was added, but the user also changed conversation send mode: its individual causal effect is not proven. iPhone may choose iMessage. Long multipart SMS and carrier delivery receipts unverified.

## Code and reproduction

- [Implementation](../../sms-bridge/outgoing.py)
- [Test or detailed evidence](../../sms-bridge/tests/test_outgoing.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
