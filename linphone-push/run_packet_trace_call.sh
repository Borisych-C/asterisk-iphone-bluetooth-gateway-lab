#!/usr/bin/env bash
set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
    printf 'run_packet_trace_call.sh must run as root\n' >&2
    exit 1
fi

trace_file="$(mktemp)"
trap 'rm -f "$trace_file"' EXIT

timeout 25 tcpdump -l -nn -s 0 -A -i enp3s0 udp port 5060 \
    > "$trace_file" 2>/dev/null &
capture_pid=$!
sleep 2

asterisk -rx \
    'channel originate PJSIP/linphone-push/sip:traveler-example@sip.linphone.org application Playback hello-world'

wait "$capture_pid" || true

printf 'Sanitized UDP/5060 signaling summary:\n'
grep -E \
    'INVITE sip:traveler-example|ACK sip:traveler-example|CANCEL sip:traveler-example|BYE sip:|SIP/2\.0 [1-6][0-9][0-9]|^From:|^To:|^Call-ID:|^Reason:|^Server:|^User-Agent:|^Contact:|^Proxy-Authenticate:|^Proxy-Authorization:' \
    "$trace_file" | \
    sed -E \
        -e 's/(response=")[^"]+"/\1[redacted]"/g' \
        -e 's/(nonce=")[^"]+"/\1[redacted]"/g' \
        -e 's/(cnonce=")[^"]+"/\1[redacted]"/g' || true
