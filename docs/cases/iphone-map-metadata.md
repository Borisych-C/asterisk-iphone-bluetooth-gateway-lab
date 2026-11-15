# Previously delivered SMS appears again after reconnect

Case: `iphone-map-metadata` · Evidence: **confirmed-local**

Search terms: MAP timestamp shifted one second duplicate SMS message handle fingerprint

## Diagnosis

The iPhone re-reported one message with a timestamp one second earlier. A metadata-based identity treated it as new.

## Resolution

Store sender/body digest and tolerate ±2 seconds; retain aliases for changed metadata keys. Do not resend old rows during migration.

## Evidence and limits

Different messages outside the window remain distinct. Two genuine identical messages from the same sender inside two seconds may coalesce. This is an explicit heuristic, not exactly-once delivery.

## Code and reproduction

- [Implementation](../../sms-bridge/bridge.py)
- [Test or detailed evidence](../../sms-bridge/tests/test_bridge.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
