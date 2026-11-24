# Asterisk · iPhone · Bluetooth gateway troubleshooting lab

**Reproducible fixes and device field notes for AI agents and humans diagnosing a home-SIM SIP gateway.** Asterisk `chan_mobile`, iPhone HFP/SCO/eSCO, BlueZ MAP SMS/iMessage, Linphone TLS/SRTP, RTP source changes, NAT and DuckDNS.

This repository is a troubleshooting knowledge base with source code, not a turnkey appliance. It documents a working local installation and its limits. Start with the symptom index; do not deploy every historical workaround.

**[Browsable case website](https://borisych-c.github.io/asterisk-iphone-bluetooth-gateway-lab/)** · **[Symptom → diagnosis → fix → test](docs/INDEX.md)** · **[Reports to maintainers](docs/UPSTREAM-REPORTS.md)** · **[Phone/client quirks](docs/DEVICE-QUIRKS.md)** · **[Agent instructions](AGENTS.md)** · **[Русский](README.ru.md)**

## Most useful entry points

| What you see | Where to start |
|---|---|
| iPhone has no Bluetooth “Show Notifications” toggle | [First MAP request, reopen device details](docs/cases/iphone-map-permission.md) |
| Call drops immediately when answered | [NULL versus temporary missing SCO audio](docs/cases/sco-false-hangup.md) |
| RTP packets arrive but one direction is silent | [SSRC/sequence history in the distro translator patch](docs/cases/rtp-source-reset.md) |
| 48-byte PCM versus 60-byte eSCO packet confusion | [Host framing is not radio packet length](docs/cases/sco-host-packet-size.md) |
| `invalid-address` although the SIP URI looks correct | [AGI field truncation at particular lengths](docs/cases/agi-field-truncation.md) |
| SMS repeats after Bluetooth reconnect | [Timestamp changed by one second](docs/cases/iphone-map-metadata.md) |
| Linphone selects another number from a contact | [`sms-` recipient alias](docs/cases/linphone-contact-selection.md) |
| Call fails with 488 after account registration | [SAVP/SAVPF profile mismatch](docs/cases/linphone-srtp-profile.md) |
| Audio or hangup fails through public address | [Port mapping and hairpin Contact](docs/cases/nat-rtp-range.md) |
| Russian SMS is unreadable on a T780P | [Empirical firmware glyph map](docs/cases/t780p-character-map.md) |

## The overall idea

Leave an iPhone with the home SIM at home. A Linux server bridges its Bluetooth calls to a traveler’s Linphone client over the internet, and bridges messages through MAP and SIP MESSAGE.

```text
incoming call: SIM → iPhone → Bluetooth → Asterisk → TLS/SRTP → Linphone
outgoing call: authenticated Linphone → Asterisk → Bluetooth → iPhone/SIM
incoming text: iPhone → MAP → durable bridge queue → TLS SIP MESSAGE → Linphone
outgoing text: authenticated SIP MESSAGE → AGI → local socket/queue → MAP → iPhone
```

The desk phone was a debugging endpoint, not a requirement for the final path. Asterisk-to-Linphone federation uses the gateway’s own domain without the user's Linphone credentials. The app still uses its service account for incoming/push; a **separate authenticated account on the home Asterisk** authorizes outgoing SIM use. Public dialing is not permission to use someone’s cellular line.

TLS/SRTP protect the applicable network legs; the gateway processes plaintext audio/text. This is not end-to-end encryption. MAP acceptance is not a delivery receipt. Charges and operator conditions depend on the user's service.

## Repository map

- `docs/issues.json`: machine-readable cases, evidence level, implementation and reproduction pointers.
- `docs/cases/`: concise English diagnostic cards; `docs/DEVICE-QUIRKS.md`: device-first navigation.
- `recovery/2026-11-14/work/`: final `chan_mobile.c`, `app_rtp_source_reset.c`, patches, C framing tests, isolated RTP test and source-only build inputs.
- `sms-bridge/`: incoming/outgoing MAP ↔ SIP bridge, AGI, durable queues, tests and installers.
- `network/`: DNS updater, public SIP examples, router/certificate scripts and diagnostics.
- `roaming/`: authenticated mobile-client route examples and probes.
- `tools/`, `research/2026-11-14-message-encoding/`: desk-phone message/glyph experiments.
- `linphone-push/`, `stage1/`: **historical/optional** credential-based and WebRTC experiments; not the final architecture.
- Top-level Russian `.txt` reports and `CONTEXT-HISTORY.md`: sanitized case narrative. Archived paths, hashes and deployment recipes are historical evidence, not current commands.
- `editorial/`: long-form background for article writers, not operational guidance.
- [Script inventory](docs/SCRIPT-INVENTORY.md): every project script with effect/risk category.
- [Build and test](docs/BUILD-AND-TEST.md) · [Privacy boundary](docs/PUBLICATION.md) · [Licenses](NOTICE.md).

## Evidence, not promises

The original environment was x86-64 Linux Mint 22.3, a distro Asterisk 20.6.0 build, BlueZ 5.72, iPhone 16 and a T780P desk phone. iOS version was not recorded. The user confirmed external incoming/outgoing calls, two-way speech, caller ID, hangup, incoming iMessage and carrier SMS, and an outgoing message from Linphone without touching the home iPhone.

The isolated RTP test changed from missing PCM in failing phases to 450/450 correct frames while retaining rejection of a genuinely late packet. The bridge has 18 regression tests. These observations do **not** establish multi-day availability, universal firmware compatibility, MMS, long multipart SMS, all roaming networks, or IPv6 call support. Current upstream bug status must be checked before applying a historical workaround.

Some failures were implementation mistakes introduced during this work, not vendor defects. Cases explicitly distinguish reproduced defects, local observations, user-reported UI behavior and unknown causes.

## Start safely

Read [AGENTS.md](AGENTS.md), find the relevant case, inspect the referenced code and run only its offline tests first. Example hostnames, accounts, phone numbers, MACs and LAN addresses are substituted, not usable credentials. Deployment scripts are case-study recipes, not safe universal installers. Some probes place real calls or send paid messages.

No live backups, credentials, message databases, packet captures, original user photos, compiled modules or private Git history are included. Updating Asterisk may change module ABI: rebuild and retest instead of copying an old `.so`.

## Discovery terms

Asterisk chan_mobile iPhone Bluetooth HFP SCO eSCO CVSD USB PCM one-way audio; RTP SSRC sequence number ast_translate NULL 2016_opus_plc.patch RtpSourceReset; BlueZ OBEX MAP PushMessage bMessage SMS iMessage; iOS Show Notifications missing Bluetooth permission; Linphone SIP federation TLS SRTP SDES SAVP SAVPF; AGI BASE64_ENCODE invalid-address; T780P CP1251 CP1252 Unicode mojibake; NAT hairpin Contact ACK BYE; DuckDNS stale AAAA IPv6 prefix; AI agent troubleshooting reproducible diagnostics.

Search/discovery mechanism and limits: [DISCOVERY.md](docs/DISCOVERY.md).
