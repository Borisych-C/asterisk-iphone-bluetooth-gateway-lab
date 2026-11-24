# Outbound SIP MESSAGE loses its explicit charset

Case `pjsip-message-charset` · **confirmed-reproduced**

## Diagnosis

The parsed Content-Type header includes media parameters, but update_content_type() copies only media type and subtype into the outgoing body.

## Resolution

Preserve parsed media parameters when constructing the outgoing message. A separate direct encoding test can isolate a legacy handset renderer.

## Evidence and limits

Ubuntu Noble 20.6.0 sent text/plain for text/plain with charset=UTF-8. The independent X-Probe-Type header retained the full value. The application/json control and both message bodies arrived intact. The same function was inspected in 22.12.0, 24.0.0 and master cfb0aa2a.

[Evidence and reproduction](../../research/message-content-type.md).

## Reports

[Asterisk #2339](https://github.com/asterisk/asterisk/issues/2339).
