# PushMessage completes but recipient has no SMS

Case: `iphone-map-outgoing` · Evidence: **observed-device**

Search terms: iPhone MAP Uploading bMessage originator vCard green bubble Not Delivered SMS iMessage

## Diagnosis

MAP completion means phone acceptance, not carrier delivery. One accepted transfer produced Not Delivered; manual SMS retry succeeded. A later new message arrived automatically after delay.

## Resolution

Use UTF-8 bMessage with originator/recipient structure; distinguish queued, submitting, handed-to-phone and unknown. Never automatically repeat an ambiguous cellular send.

## Evidence and limits

One accepted upload was followed by a delivery failure on the phone. A later new message arrived automatically. The originator vCard and phone send mode both changed. Long multipart messages and carrier receipts remain unverified. BlueZ #2897 requests an API documentation cross-reference.

## Code and reproduction

- [Implementation](../../sms-bridge/outgoing.py)
- [Test or detailed evidence](../../sms-bridge/tests/test_outgoing.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.

## Reports

[BlueZ documentation proposal #2897](https://github.com/bluez/bluez/issues/2897).
