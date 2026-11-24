# iPhone Bluetooth Show Notifications switch is missing

Case: `iphone-map-permission` · Evidence: **observed-device**

Search terms: iOS iPhone 16 MAP OBEX MessageAccess permission access denied missing toggle

## Diagnosis

Working HFP pairing did not expose MAP permission initially. The first MAP request returned access denied. After reopening the Bluetooth device details the switch appeared.

## Resolution

Pair/connect; issue one MAP access request; reopen Settings → Bluetooth → device info; enable Show Notifications. Then retry reading. Do not repeatedly re-pair as the first response.

## Evidence and limits

Observed on one iPhone 16, with the original iOS build unrecorded. Enabling Show Notifications allowed reading. Outgoing PushMessage was tested separately. Apple acknowledged the private product feedback without a public case number.

## Code and reproduction

- [Implementation](../../sms-bridge/bridge.py)
- [Test or detailed evidence](../../SMS-BRIDGE.txt)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.

## Reports

[Apple iPhone Product Feedback](https://www.apple.com/feedback/iphone/).
