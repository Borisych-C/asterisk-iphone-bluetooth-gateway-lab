# Script inventory

All project-authored scripts are retained, including historical branches. Upstream build-input code and browser vendor dependencies are indexed by their directory/manifest rather than individually here. Classification is conservative and does not grant execution permission.

| Source | Effect / scope |
|---|---|
| [apply_remote_hairpin.sh](../apply_remote_hairpin.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [apply_remote_vpn_changes.sh](../apply_remote_vpn_changes.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [diagnostics/2026-11-14-linphone-612/capture-sip-history.py](../diagnostics/2026-11-14-linphone-612/capture-sip-history.py) | Diagnostic / may access live host and private data |
| [diagnostics/2026-11-14-linphone-federation/capture.py](../diagnostics/2026-11-14-linphone-federation/capture.py) | Diagnostic / may access live host and private data |
| [linphone-push/deploy_auth.sh](../linphone-push/deploy_auth.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [linphone-push/deploy_test.sh](../linphone-push/deploy_test.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [linphone-push/keyring_credentials.py](../linphone-push/keyring_credentials.py) | Credential/UI helper — private local use only |
| [linphone-push/packet_trace_call.sh](../linphone-push/packet_trace_call.sh) | Diagnostic / may access live host and private data |
| [linphone-push/remote_install_auth.sh](../linphone-push/remote_install_auth.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [linphone-push/remote_install_test.sh](../linphone-push/remote_install_test.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [linphone-push/remote_switch_incoming.sh](../linphone-push/remote_switch_incoming.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [linphone-push/run_packet_trace_call.sh](../linphone-push/run_packet_trace_call.sh) | Diagnostic / may access live host and private data |
| [linphone-push/run_test_call.sh](../linphone-push/run_test_call.sh) | MAY send real traffic, calls or messages — inspect first |
| [linphone-push/run_trace_call.sh](../linphone-push/run_trace_call.sh) | Diagnostic / may access live host and private data |
| [linphone-push/run_verify_credentials.sh](../linphone-push/run_verify_credentials.sh) | Diagnostic / may access live host and private data |
| [linphone-push/store_credentials.sh](../linphone-push/store_credentials.sh) | Credential/UI helper — private local use only |
| [linphone-push/switch_incoming.sh](../linphone-push/switch_incoming.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [linphone-push/test_call.sh](../linphone-push/test_call.sh) | MAY send real traffic, calls or messages — inspect first |
| [linphone-push/trace_call.sh](../linphone-push/trace_call.sh) | Diagnostic / may access live host and private data |
| [linphone-push/verify_credentials.sh](../linphone-push/verify_credentials.sh) | Diagnostic / may access live host and private data |
| [network/duckdns/test_updater.py](../network/duckdns/test_updater.py) | Offline validation / synthetic fixtures |
| [network/duckdns/update_duckdns.sh](../network/duckdns/update_duckdns.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [network/public-sip/asterisk-public-cert-deploy.sh](../network/public-sip/asterisk-public-cert-deploy.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [network/public-sip/capture-call.py](../network/public-sip/capture-call.py) | Diagnostic / may access live host and private data |
| [network/public-sip/deploy-server.py](../network/public-sip/deploy-server.py) | MUTATES host/services/network/DNS — adapt and authorize first |
| [network/public-sip/probe.py](../network/public-sip/probe.py) | MAY send real traffic, calls or messages — inspect first |
| [network/public-sip/router-forwarding.py](../network/public-sip/router-forwarding.py) | Inspect source before execution; environment-specific helper |
| [recovery/2026-11-14/reports/check.py](../recovery/2026-11-14/reports/check.py) | Offline validation / synthetic fixtures |
| [recovery/2026-11-14/reports/core-trace-check.py](../recovery/2026-11-14/reports/core-trace-check.py) | Diagnostic / may access live host and private data |
| [recovery/2026-11-14/reports/rtp-check.py](../recovery/2026-11-14/reports/rtp-check.py) | Inspect source before execution; environment-specific helper |
| [recovery/2026-11-14/reports/trace-check.py](../recovery/2026-11-14/reports/trace-check.py) | Diagnostic / may access live host and private data |
| [recovery/2026-11-14/work/build-source-reset.py](../recovery/2026-11-14/work/build-source-reset.py) | Writes local build/source output; no installation implied |
| [recovery/2026-11-14/work/deploy-source-reset.py](../recovery/2026-11-14/work/deploy-source-reset.py) | MUTATES host/services/network/DNS — adapt and authorize first |
| [recovery/2026-11-14/work/deploy.py](../recovery/2026-11-14/work/deploy.py) | MUTATES host/services/network/DNS — adapt and authorize first |
| [recovery/2026-11-14/work/isolated-rtp.py](../recovery/2026-11-14/work/isolated-rtp.py) | Inspect source before execution; environment-specific helper |
| [recovery/2026-11-14/work/prepare.py](../recovery/2026-11-14/work/prepare.py) | Writes local build/source output; no installation implied |
| [research/2026-11-14-message-encoding/send-controls-00-31.py](../research/2026-11-14-message-encoding/send-controls-00-31.py) | MAY send real traffic, calls or messages — inspect first |
| [roaming/check-access.py](../roaming/check-access.py) | Diagnostic / may access live host and private data |
| [roaming/deploy.py](../roaming/deploy.py) | MUTATES host/services/network/DNS — adapt and authorize first |
| [roaming/probe-echo.py](../roaming/probe-echo.py) | MAY send real traffic, calls or messages — inspect first |
| [roaming/show-client-settings.py](../roaming/show-client-settings.py) | Credential/UI helper — private local use only |
| [scripts/check.py](../scripts/check.py) | Offline validation / synthetic fixtures |
| [sms-bridge/asterisk/install-root.py](../sms-bridge/asterisk/install-root.py) | MUTATES host/services/network/DNS — adapt and authorize first |
| [sms-bridge/bridge.py](../sms-bridge/bridge.py) | Production integration; network/queue/message side effects |
| [sms-bridge/install.sh](../sms-bridge/install.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [sms-bridge/outgoing.py](../sms-bridge/outgoing.py) | Production integration; network/queue/message side effects |
| [sms-bridge/research/probe-auth-message.py](../sms-bridge/research/probe-auth-message.py) | MAY send real traffic, calls or messages — inspect first |
| [sms-bridge/research/probe-outgoing.py](../sms-bridge/research/probe-outgoing.py) | MAY send real traffic, calls or messages — inspect first |
| [sms-bridge/research/probe-sip-message.py](../sms-bridge/research/probe-sip-message.py) | MAY send real traffic, calls or messages — inspect first |
| [sms-bridge/research/seed-legacy-identities.py](../sms-bridge/research/seed-legacy-identities.py) | Inspect source before execution; environment-specific helper |
| [sms-bridge/research/trace-message-headers.py](../sms-bridge/research/trace-message-headers.py) | Diagnostic / may access live host and private data |
| [sms-bridge/sms-submit.agi](../sms-bridge/sms-submit.agi) | Production integration; network/queue/message side effects |
| [sms-bridge/tests/test_agi.py](../sms-bridge/tests/test_agi.py) | Offline validation / synthetic fixtures |
| [sms-bridge/tests/test_bridge.py](../sms-bridge/tests/test_bridge.py) | Offline validation / synthetic fixtures |
| [sms-bridge/tests/test_outgoing.py](../sms-bridge/tests/test_outgoing.py) | Offline validation / synthetic fixtures |
| [stage1/browser-phone/phone.js](../stage1/browser-phone/phone.js) | Historical browser source/overlay — optional PWA branch |
| [stage1/browser-phone/phone.min.js](../stage1/browser-phone/phone.min.js) | Historical browser source/overlay — optional PWA branch |
| [stage1/browser-phone/stage1-bootstrap.js](../stage1/browser-phone/stage1-bootstrap.js) | Historical browser source/overlay — optional PWA branch |
| [stage1/browser-phone/stage1-probe.js](../stage1/browser-phone/stage1-probe.js) | MAY send real traffic, calls or messages — inspect first |
| [stage1/browser-phone/stage1-runtime.js](../stage1/browser-phone/stage1-runtime.js) | Historical browser source/overlay — optional PWA branch |
| [stage1/browser-phone/sw.js](../stage1/browser-phone/sw.js) | Historical browser source/overlay — optional PWA branch |
| [stage1/check_chrome.js](../stage1/check_chrome.js) | Inspect source before execution; environment-specific helper |
| [stage1/deploy_remote.sh](../stage1/deploy_remote.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [stage1/read_remote_root.sh](../stage1/read_remote_root.sh) | Diagnostic / may access live host and private data |
| [stage1/remote_install.sh](../stage1/remote_install.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [stage1/vpn-dns/remote_install.sh](../stage1/vpn-dns/remote_install.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [stage1/vpn-hairpin/asterisk-pwa-hairpin](../stage1/vpn-hairpin/asterisk-pwa-hairpin) | MUTATES host/services/network/DNS — adapt and authorize first |
| [stage1/vpn-hairpin/clear_stale_duckdns_aaaa.sh](../stage1/vpn-hairpin/clear_stale_duckdns_aaaa.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [stage1/vpn-hairpin/remote_install.sh](../stage1/vpn-hairpin/remote_install.sh) | MUTATES host/services/network/DNS — adapt and authorize first |
| [tools/send-byte-chart.py](../tools/send-byte-chart.py) | MAY send real traffic, calls or messages — inspect first |
| [tools/send-phone-test.py](../tools/send-phone-test.py) | MAY send real traffic, calls or messages — inspect first |

| [scripts/build-doc-site.py](../scripts/build-doc-site.py) | Writes static documentation HTML only; no network or deployment |
