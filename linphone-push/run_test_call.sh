#!/usr/bin/env bash
set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
    printf 'run_test_call.sh must run as root\n' >&2
    exit 1
fi

log_file="/var/log/asterisk/full"
start_line=0
if [[ -f "$log_file" ]]; then
    start_line="$(wc -l < "$log_file")"
fi

asterisk -rx 'pjsip set logger on'
trap "asterisk -rx 'pjsip set logger off' >/dev/null 2>&1 || true" EXIT

printf 'Starting one Linphone push test call now. Answer to hear the hello-world prompt.\n'
asterisk -rx \
    'channel originate PJSIP/linphone-push/sip:traveler-example@sip.linphone.org application Playback hello-world'

sleep 50
asterisk -rx 'core show channels'
asterisk -rx 'pjsip set logger off'
trap - EXIT

if [[ -f "$log_file" ]]; then
    printf '\nRelevant Asterisk log lines:\n'
    tail -n "+$((start_line + 1))" "$log_file" | \
        grep -E 'traveler-example|linphone-push|SIP/[12]\.0 [1-6][0-9][0-9]|Everyone is busy|answered|failed|No route|Forbidden|Unauthorized' || true
fi

asterisk -rx 'mobile show devices'

