#!/usr/bin/env bash
set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
    printf 'run_trace_call.sh must run as root\n' >&2
    exit 1
fi

trace_file="$(mktemp)"
trap 'rm -f "$trace_file"' EXIT

{
    sleep 1
    printf 'pjsip set logger on\n'
    sleep 1
    printf 'channel originate PJSIP/linphone-push/sip:traveler-example@sip.linphone.org application Playback hello-world\n'
    sleep 20
    printf 'pjsip set logger off\n'
    printf 'quit\n'
} | asterisk -rvvvvv > "$trace_file" 2>&1

printf 'Sanitized SIP call trace:\n'
grep -E \
    '^(<---|---)|INVITE sip:|SIP/[12]\.0 [1-6][0-9][0-9]|From:|To:|Contact:|Call-ID:|WWW-Authenticate:|Proxy-Authenticate:|Everyone is busy|answered|failed|No route|Forbidden|Unauthorized|Connected to Asterisk|Disconnected from Asterisk' \
    "$trace_file" | \
    sed -E \
        -e 's/(Authorization:.*response=")[^"]+"/\1[redacted]"/' \
        -e 's/(Proxy-Authorization:.*response=")[^"]+"/\1[redacted]"/' \
        -e 's/(cnonce=")[^"]+"/\1[redacted]"/' || true

