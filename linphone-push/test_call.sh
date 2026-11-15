#!/usr/bin/env bash
set -euo pipefail

remote_host="192.168.50.10"
remote_script="/tmp/asterisk-linphone-push-payload/run_test_call.sh"
credential_helper="$(cd "$(dirname "$0")" && pwd)/keyring_credentials.py"

sudo_password="$($credential_helper lookup \
    --host 192.168.50.10 --username gateway --kind sudo-password)"
trap 'unset sudo_password' EXIT

printf '%s\n' "$sudo_password" | ssh -o BatchMode=yes "$remote_host" \
    "sudo -S -p '' '$remote_script'"
