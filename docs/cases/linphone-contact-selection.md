# SMS goes to a different number from the contact card

Case: `linphone-contact-selection` · Evidence: **user-observed**

Search terms: Linphone iOS address book multiple numbers SIP MESSAGE sms- prefix

## Diagnosis

User observed Linphone selecting another number from a multi-number contact. Separate malformed @ input also occurred. No upstream client code defect was independently proven.

## Resolution

Use sms-972501234567@home.example.net on the authenticated Home SIM account, select that exact SIP result. Strip sms- server-side before number normalization.

## Evidence and limits

The prefix workaround worked on the observed iOS 6.2.2 client. Source inspection on 6.2.2 and 6.2.4 found recipient rows omitting an address and a SIPS display formatting issue. The exact taps leading to the wrong number were not recorded.

## Code and reproduction

- [Implementation](../../sms-bridge/outgoing.py)
- [Test or detailed evidence](../../sms-bridge/tests/test_outgoing.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.

## Reports

[Linphone iOS #1055](https://github.com/BelledonneCommunications/linphone-iphone/issues/1055).
