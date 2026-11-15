# Troubleshooting index

Start with the symptom, not the component blamed first. Evidence levels distinguish reproduced defects, local observations and user reports.

| Symptom | Case | Evidence |
|---|---|---|
| Call disconnects immediately on answer | [sco-false-hangup](cases/sco-false-hangup.md) | confirmed-reproduced |
| One-way audio despite successful Bluetooth writes | [sco-host-packet-size](cases/sco-host-packet-size.md) | confirmed-local |
| RTP arrives but outgoing Bluetooth audio stops intermittently | [rtp-source-reset](cases/rtp-source-reset.md) | confirmed-reproduced |
| iPhone Bluetooth Show Notifications switch is missing | [iphone-map-permission](cases/iphone-map-permission.md) | observed-device |
| Previously delivered SMS appears again after reconnect | [iphone-map-metadata](cases/iphone-map-metadata.md) | confirmed-local |
| PushMessage completes but recipient has no SMS | [iphone-map-outgoing](cases/iphone-map-outgoing.md) | observed-device |
| SMS goes to a different number from the contact card | [linphone-contact-selection](cases/linphone-contact-selection.md) | user-observed |
| invalid-address even when MESSAGE(to) is correct | [agi-field-truncation](cases/agi-field-truncation.md) | confirmed-local |
| Registered client immediately receives 488 or cannot establish media | [linphone-srtp-profile](cases/linphone-srtp-profile.md) | confirmed-local |
| Caller number exists in SIP but is not displayed | [caller-id-whitespace](cases/caller-id-whitespace.md) | confirmed-local |
| Call connects with missing audio or does not hang up | [nat-rtp-range](cases/nat-rtp-range.md) | confirmed-local |
| Public name points to unavailable IPv6 | [dns-stale-ipv6](cases/dns-stale-ipv6.md) | confirmed-local |
| Russian SIP MESSAGE is mojibake despite Russian menus | [t780p-character-map](cases/t780p-character-map.md) | observed-device |
| SIP URI pasted into search fails or uses unexpected transport | [linphone-uri-input](cases/linphone-uri-input.md) | observed-client |
| Seven service messages appear at once after one SMS | [notification-burst](cases/notification-burst.md) | confirmed-sender-only |

Machine-readable index: [issues.json](issues.json). Device-first view: [DEVICE-QUIRKS.md](DEVICE-QUIRKS.md).
