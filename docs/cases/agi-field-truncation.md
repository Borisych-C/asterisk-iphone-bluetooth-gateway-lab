# invalid-address even when MESSAGE(to) is correct

Case: `agi-field-truncation` · Evidence: **confirmed-local**

Search terms: Asterisk AGI BASE64_ENCODE truncated .org .o UTF-8 exact LEN multiline

## Diagnosis

The original MESSAGE(to) was complete, but the tested BASE64_ENCODE/AGI path lost trailing bytes at some lengths. Short check addresses masked the problem.

## Resolution

Read exact raw byte length reported by LEN; validate delimiters and UTF-8. Keep message text out of argv/logs. Do not attribute this to the Base64 algorithm itself.

## Evidence and limits

Live authenticated TLS check verified hash equality of URI, Unicode multiline body, Call-ID and CSeq. Regression tests vary lengths and embedded delimiters. Root cause inside the specific Base64 implementation was not fully upstream-localized.

## Code and reproduction

- [Implementation](../../sms-bridge/sms-submit.agi)
- [Test or detailed evidence](../../sms-bridge/tests/test_agi.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
