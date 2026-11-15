# Stage 1 deployment

This directory contains the isolated Browser-Phone/WebRTC probe described in
`../PWA_PHONE_RESEARCH_CONTEXT.md`.

Physical iPhone testing is currently paused at the HTTPS-origin access layer.
The verified Private Relay/DNS behavior, temporary VPN changes and exact resume
point are documented in `../STAGE1_IOS_ACCESS_PAUSE.md`.

Deployed URL:

```text
https://home.example.net/flacmusic/phone-probe/
```

The deployment uses endpoint `1099`, WSS path
`/flacmusic/asterisk-ws`, echo extension `600`, and controlled HFP test
extension `611`. The SIP password is generated on `.128` and is never stored
in this workspace.

Browser-Phone is pinned to commit
`33902782876259957b18f9ca71f811ae0f29b6b3` (version 0.3.29). Its runtime
dependencies are vendored under `browser-phone/vendor` so the probe does not
need third-party CDNs.

The installer creates timestamped backups under
`/var/backups/asterisk-pwa-stage1/` and deploys each web build to a versioned
directory below `/var/www`, switching only the
`/var/www/asterisk-pwa-stage1` symlink.
