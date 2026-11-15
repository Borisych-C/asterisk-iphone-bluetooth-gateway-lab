> ИСТОРИЧЕСКИЙ МАТЕРИАЛ, август 2026. Приостановленное исследование PWA/WebRTC.
> Не описывает действующий маршрут Linphone. Текущее состояние: [CONTEXT.md](CONTEXT.md).
> Статус старой инфраструктуры сейчас отдельно не проверялся.

# Stage 1: iOS WebRTC PWA results

Deployment date: 2026-08-09

Status: infrastructure deployed and automatically validated from a separate
LAN browser. Physical iPhone testing is paused before the WebRTC matrix because
Safari/iCloud Private Relay cannot currently reach the VPN-only HTTPS origin.
The complete access diagnosis and decision point are recorded in
`STAGE1_IOS_ACCESS_PAUSE.md`.

## Deployed probe

- URL: `https://home.example.net/flacmusic/phone-probe/`
- PJSIP endpoint: `1099`
- Echo: `600`
- Controlled Partner IVR/HFP route: `611`
- Browser-Phone: 0.3.29, commit `33902782876259957b18f9ca71f811ae0f29b6b3`
- Web Push, Queue and late attach: not part of Stage 1
- Active server release: `/var/www/asterisk-pwa-stage1-20260809-204347`
- Latest configuration backup: `/var/backups/asterisk-pwa-stage1/20260809-204347`

## VPN split DNS

The first physical iPhone attempt did not reach the home Apache server. Public
DNS resolved `home.example.net` to `192.0.2.5`; that endpoint supplied
an unrelated Microsoft certificate and then returned `400 Invalid URL` after
the certificate warning was bypassed. There was no matching iPhone request in
the home Apache access log. The earlier automated browser validation had used
an explicit hostname-to-`192.168.50.10` mapping, so it did not exercise public
DNS.

On 2026-08-09 a VPN-only split DNS resolver was deployed on the AmneziaWG/HA
host:

- DNS server: `10.77.77.1`, listening on TCP/UDP 53 only on `awg0`.
- Local record: `home.example.net` -> `192.168.50.10`.
- AAAA for that name is intentionally answered with no data, preventing a
  public IPv6 route from bypassing the private IPv4 record.
- Other DNS queries are forwarded to the home resolver at `192.168.50.1`.
- `dnsmasq` configuration test, local A/AAAA queries, external forwarding and
  HTTPS access to the PWA all passed.
- The firewall accepts input from `awg0`; VPN-to-LAN traffic is masqueraded as
  `192.168.50.20`, which is already allowed by the Apache Stage 1 ACL.
- Active DNS configuration: `/etc/dnsmasq.d/asterisk-pwa-vpn.conf` on
  `192.168.50.20`.
- Latest DNS backup: `/var/backups/asterisk-pwa-vpn-dns/20260809-210748`.

The original iPhone profiles were left unchanged. Ready-to-import copies with
`DNS = 10.77.77.1` are:

- `/home/gateway/vpn/iphone-amneziawg-split-dns.conf` for LAN-only routing.
- `/home/gateway/vpn/iphone-amneziawg-full-split-dns.conf` for full-tunnel
  routing.

Physical packet captures subsequently proved that Safari did not use this DNS
resolver. With full tunnel active, encrypted DNS/relay traffic went to public
UDP/443 endpoints, while the home Apache received no iPhone request. A narrow
VPN hairpin for TCP 443/8443 also saw no origin connection after the stale
public AAAA record was removed. Do not treat split DNS or the hairpin as a
working iPhone access solution. See `STAGE1_IOS_ACCESS_PAUSE.md`.

## Automated validation completed

The probe was opened in a clean headless Chrome profile on another LAN host
(`192.168.50.107`), using fake microphone input only for transport validation.

- HTTPS certificate validation passed against the deployed Apache virtual host.
- The page, manifest, service worker, SIP.js and diagnostic script returned HTTP 200.
- The service worker installed and controlled the page.
- WSS returned `101 Switching Protocols` with subprotocol `sip`.
- SIP UserAgent connected and endpoint `1099` registered successfully.
- A call to Echo `600` reached SIP state `Established`.
- ICE and PeerConnection reached `connected`.
- Asterisk advertised the correct LAN candidate `192.168.50.10`.
- At the final sample, inbound RTP had 1,738 packets and outbound RTP had
  1,739 packets; inbound packet loss was zero and jitter was about 1 ms.
- Browser Hangup terminated the SIP session normally.
- After an Asterisk restart, the browser detected disconnect, reconnected and
  registered automatically.
- Bluetooth subsequently reported the home iPhone as paired, trusted and
  connected. The physical HFP call through `611` remains an iPhone test item.

An initial automated Echo attempt exposed a configuration defect: binding the
PJSIP WSS transport object to `127.0.0.1` also bound its WebRTC RTP socket to
loopback. The transport object now binds to `0.0.0.0`, while the actual Asterisk
HTTP/WebSocket listener remains restricted to `127.0.0.1:8088` and is exposed
only through the VPN-restricted Apache proxy. The repeated Echo test then
passed with two-way RTP.

## Baseline

| Test | Result | Notes |
|---|---|---|
| Install from Safari using Add to Home Screen | pending | |
| Standalone launch | pending | |
| SIP/WSS registration | automated pass | Must repeat from installed iPhone PWA |
| Echo 600, foreground | automated transport pass | Real microphone/playback pending |
| HFP route 611, foreground | pending | |
| New call after normal hangup | pending | |

## Background and interruption matrix

For audio, record `both`, `downlink only`, `uplink only`, or `none`.

| Scenario | Audio while away | SIP/RTP after return | Controls work | Next call works | Notes |
|---|---|---|---|---|---|
| Other app, 5 seconds | pending | pending | pending | pending | |
| Other app, 30 seconds | pending | pending | pending | pending | |
| Other app, 120 seconds | pending | pending | pending | pending | |
| Lock screen, 5 seconds | pending | pending | pending | pending | |
| Lock screen, 30 seconds | pending | pending | pending | pending | |
| Lock screen, 120 seconds | pending | pending | pending | pending | |
| Repeated background/foreground cycles | pending | pending | pending | pending | |
| Wi-Fi to cellular with VPN | pending | pending | pending | pending | |
| Cellular to Wi-Fi with VPN | pending | pending | pending | pending | |
| VPN loss, 5 seconds | pending | pending | pending | pending | |
| VPN loss, 30 seconds | pending | pending | pending | pending | |
| Control Center | pending | pending | pending | pending | |
| Siri interruption | pending | pending | pending | pending | |
| Native cellular call interruption | pending | pending | pending | pending | |

## Evidence to preserve

- Copy the persistent `Stage 1 log` from the floating button after each group.
- Record the exact iPhone model and iOS version.
- Record whether the test was launched from Safari or the Home Screen icon.
- Record VPN and access-network state.
- Correlate client timestamps with Asterisk channel/contact/RTP observations.

## Decision

- Current decision: paused before physical WebRTC testing.
- Final classification: `GO`, `GO with foreground limitation`, or `NO-GO`.

## Next physical action

No physical action is pending while the user considers the hostname design.
Resume from `STAGE1_IOS_ACCESS_PAUSE.md`: decide whether the existing
`home.example.net` may return private A `192.168.50.10`, or create a
dedicated VPN-only hostname and certificate. Do not ask the user to disable
Private Relay or encrypted DNS as a normal operating requirement.
