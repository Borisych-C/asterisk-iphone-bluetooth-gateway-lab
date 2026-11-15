# Caller number exists in SIP but is not displayed

Case: `caller-id-whitespace` · Evidence: **confirmed-local**

Search terms: iPhone Bluetooth CNAM eight spaces display name CALLERID num Linphone

## Diagnosis

From URI contained the number but Bluetooth CNAM supplied eight spaces as display name.

## Resolution

Set caller ID display name from number before Dial, preserving privacy policy.

## Evidence and limits

User confirmed number on external incoming call; empty display data is not evidence of missing signaling.

## Code and reproduction

- [Implementation](../../roaming/config/extensions_roaming.conf)
- [Test or detailed evidence](../../ROAMING.txt)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
