#!/usr/bin/env bash
set -euo pipefail

remote_host="192.168.50.10"
remote_payload="/tmp/asterisk-linphone-push-payload"
credential_helper="$(cd "$(dirname "$0")" && pwd)/keyring_credentials.py"

rsync -a --delete ./linphone-push/ "$remote_host:$remote_payload/"
rsync -a ./config/extensions_local.conf \
    "$remote_host:$remote_payload/config/extensions_local.conf"

sudo_password="$($credential_helper lookup \
    --host 192.168.50.10 --username gateway --kind sudo-password)"
if [[ -z "$sudo_password" ]]; then
    printf 'Server sudo password is missing from the keyring.\n' >&2
    exit 1
fi
trap 'unset sudo_password' EXIT

printf '%s\n' "$sudo_password" | ssh -o BatchMode=yes "$remote_host" \
    "sudo -S -p '' '$remote_payload/remote_switch_incoming.sh' '$remote_payload'"

