# Security and privacy

This is case-study code, not a hardened commercial gateway. Never expose an unauthenticated cellular/SMS relay. Use separate authenticated contexts for paid outgoing actions, preserve TLS certificate validation and appropriate SRTP, and constrain call/message destinations.

Do not publish live SIP/AGI/Bluetooth traces or queue databases. SIP success and MAP completion are not proof of recipient delivery. Unknown outgoing results intentionally do not auto-retry. Phone numbers in examples are synthetic and must not be dialed.

No private vulnerability mailbox has been configured for this unpublished candidate. When a remote is created, enable a private reporting channel before accepting sensitive reports. Do not put secrets in public issues.
