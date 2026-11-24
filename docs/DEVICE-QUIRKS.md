# Phone and client field notes

These are observed device behaviors, not universal manufacturer guarantees. Hardware: iPhone 16, model-labelled T780P desk phone, USB Bluetooth adapter. Tested Linphone UI was 6.2.2; the iOS version was not preserved. Do not invent a firmware compatibility matrix.

## iPhone 16

1. **Missing permission switch:** first MAP access was rejected; reopening Bluetooth device info then exposed **Show Notifications**. Enable it and retry. This was the message access permission, not a separately observed “allow sending SMS” toggle. [Exact sequence](cases/iphone-map-permission.md).
2. **Working calls do not prove MAP access.** HFP and message permissions are distinct.
3. **SCO replacement on answer:** observed 160–170 ms between old and new audio socket; a call need not end. [Read semantics](cases/sco-false-hangup.md).
4. **Host/audio and radio packet sizes differ.** Observed 48-byte host PCM versus 60-byte radio values. [Framing](cases/sco-host-packet-size.md).
5. **Message timestamp can shift after reconnect:** one second caused a duplicate. [Deduplication and tradeoff](cases/iphone-map-metadata.md).
6. **Blank caller name may be spaces:** the number existed, but eight spaces obscured it. [Caller ID](cases/caller-id-whitespace.md).
7. **MAP upload accepted ≠ delivered:** an accepted message showed Not Delivered; later automatic delivery succeeded. iMessage and ordinary SMS were tested separately. [Sending](cases/iphone-map-outgoing.md).
8. **Speaker/Bluetooth switch is a diagnostic comparison, not a repair.** Speech through the iPhone speaker proves that path works; it does not alone identify the failing Bluetooth component.

## Linphone on iPhone

- A contact with several numbers may select a different number in the observed workflow; explicit `sms-` SIP addresses bypassed that behavior. [Contact selection](cases/linphone-contact-selection.md).
- Search-field input and API URI syntax are different user workflows; clearing the field mattered. [URI input](cases/linphone-uri-input.md).
- Different account/routes offered different SAVP/SAVPF profiles. [Encryption profile](cases/linphone-srtp-profile.md).
- Locked-screen push was checked in a short real scenario, not after days of sleep.
- Seven notices appeared at once, but server send times differed; the batching layer remains unknown. [Notification burst](cases/notification-burst.md).

## T780P desk phone

The device label alone did not identify the manufacturer. The service request went to LVswitch, whose T780 product family matched the documented hardware and firmware identifiers. Russian menus did not imply Unicode SIP-message display. Bytes were photographed and mapped empirically; extended glyphs improved Cyrillic approximation. NUL truncated text and most control bytes produced no useful glyphs. [Character table](cases/t780p-character-map.md). Original photos/device web dumps are intentionally not published.

The desk phone was a diagnostic endpoint, not required in the final roaming topology. The final Linphone text path preserves Russian and Hebrew without transliteration.
