# Registered client immediately receives 488 or cannot establish media

Case: `linphone-srtp-profile` · Evidence: **confirmed-local**

Search terms: Linphone third-party account RTP/SAVP RTP/SAVPF use_avpf SRTP SDES TLS

## Diagnosis

The new third-party account offered SAVP while its endpoint expected SAVPF. A different route of the same client offered a different profile.

## Resolution

Match SDP per endpoint; for the observed third-party account use_avpf=no, keep mandatory SDES SRTP and TLS. Do not disable encryption to hide profile mismatch.

## Evidence and limits

Authenticated echo and real calls passed. Do not copy one endpoint profile to all Linphone routes.

## Code and reproduction

- [Implementation](../../roaming/config/pjsip_roaming.conf)
- [Test or detailed evidence](../../roaming/probe-echo.py)

Read [agent instructions](../../AGENTS.md) before executing scripts. A test may place a real call, send SMS or change a live system; inspect its effect first.
