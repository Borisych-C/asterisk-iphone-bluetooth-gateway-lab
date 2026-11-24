# Outbound PJSIP MESSAGE loses its media-type parameters

An isolated Ubuntu Noble Asterisk 20.6.0 process sent two out-of-dialog SIP MESSAGE requests to a loopback UDP receiver. The text body was the same seven ASCII bytes in both requests. A second header echoed the stored dialplan value so that the test also checked semicolon escaping in extensions.conf.

| Dialplan value and received X-Probe-Type | Received Content-Type | Body |
| --- | --- | --- |
| `text/plain; charset=UTF-8` | `text/plain` | `fixture` |
| `application/json` | `application/json` | `fixture` |

In an isolated Asterisk with an endpoint called `sink` pointing to a local receiver, execute the following dialplan. The backslash preserves the literal semicolon in extensions.conf. Read the outgoing packet at the receiver.

```asterisk
exten => check,1,Answer()
 same => n,Set(MESSAGE_DATA(Content-Type)=text/plain\; charset=UTF-8)
 same => n,Set(MESSAGE_DATA(X-Probe-Type)=${MESSAGE_DATA(Content-Type)})
 same => n,Set(MESSAGE(body)=fixture)
 same => n,MessageSend(pjsip:sink)
 same => n,Hangup()
```

Repeat with `application/json` in the first Set. The test receiver returned SIP 200 for each request. The source of [update_content_type](https://github.com/asterisk/asterisk/blob/cfb0aa2a84a2c78a64c8764b213bfd0623975596/res/res_pjsip_messaging.c#L647-L678) parses the header then copies only the type and subtype. We checked the same function on tags 22.12.0, 24.0.0 and that master revision. The packet capture described above used the 20.6.0 distribution build.

Explicit charset signalling is relevant to our legacy desk-phone tests. That phone also displayed direct UTF-8 SIP MESSAGE incorrectly when the client sent a charset explicitly, so restoring this parameter alone would not establish a firmware fix.
