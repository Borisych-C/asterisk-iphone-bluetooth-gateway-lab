# invalid-address even when MESSAGE(to) is correct

Case: `agi-field-truncation` · Evidence: **confirmed-local**

Search terms: Asterisk AGI BASE64_ENCODE truncated .org .o UTF-8 exact LEN multiline

## Diagnosis

The original MESSAGE(to) was complete, but the tested BASE64_ENCODE/AGI path lost trailing bytes at some lengths. Short check addresses masked the problem.

## Resolution

Read exact raw byte length reported by LEN; validate delimiters and UTF-8. Keep message text out of argv/logs. Do not attribute this to the Base64 algorithm itself.

## Evidence and limits

The upstream buffer allocation defect is tracked in Asterisk #940 and fixed by #941. Tag 20.6.0 has the old sizing formula, and 20.11.0 has the correction. The separate gateway workaround was checked for byte equality of the full URI, multiline Unicode body, Call-ID and CSeq over authenticated TLS.

## Code and reproduction

- [Implementation](../../sms-bridge/sms-submit.agi)
- [Test or detailed evidence](../../sms-bridge/tests/test_agi.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.

## Reports

[Asterisk #940](https://github.com/asterisk/asterisk/issues/940) · [Merged correction #941](https://github.com/asterisk/asterisk/pull/941).
