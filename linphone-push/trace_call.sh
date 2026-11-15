#!/usr/bin/env bash
set -euo pipefail

remote_host="192.168.50.10"
remote_payload="/tmp/asterisk-linphone-push-payload"
credential_helper="$(cd "$(dirname "$0")" && pwd)/keyring_credentials.py"

rsync -a ./linphone-push/run_trace_call.sh \
    "$remote_host:$remote_payload/run_trace_call.sh"

sudo_password="$($credential_helper lookup \
    --host 192.168.50.10 --username gateway --kind sudo-password)"
trap 'unset sudo_password' EXIT

printf '%s\n' "$sudo_password" | ssh -o BatchMode=yes "$remote_host" \
    "sudo -S -p '' '$remote_payload/run_trace_call.sh'"
