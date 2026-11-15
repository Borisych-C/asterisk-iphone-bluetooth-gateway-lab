#!/usr/bin/env bash
set -euo pipefail

credential_helper="$(cd "$(dirname "$0")" && pwd)/keyring_credentials.py"
remote_host="192.168.50.10"

linphone_password="$(zenity --password --title='Linphone password: traveler-example')"
if [[ -z "$linphone_password" ]]; then
    printf 'Linphone password entry cancelled.\n' >&2
    exit 1
fi

sudo_password="$(zenity --password --title='sudo password: gateway@192.168.50.10')"
if [[ -z "$sudo_password" ]]; then
    printf 'Server sudo password entry cancelled.\n' >&2
    unset linphone_password
    exit 1
fi
trap 'unset linphone_password sudo_password' EXIT

if ! printf '%s\n' "$sudo_password" | ssh -o BatchMode=yes "$remote_host" \
    "sudo -S -p '' -v"; then
    printf 'The sudo password for %s was rejected; nothing was stored.\n' "$remote_host" >&2
    exit 2
fi

printf '%s\n' "$linphone_password" | "$credential_helper" store \
    --host sip.linphone.org \
    --username traveler-example \
    --kind linphone-password \
    --label 'Asterisk gateway: Linphone traveler-example'

printf '%s\n' "$sudo_password" | "$credential_helper" store \
    --host 192.168.50.10 \
    --username gateway \
    --kind sudo-password \
    --label 'Asterisk gateway: sudo gateway@192.168.50.10'

unset linphone_password sudo_password

linphone_present="$($credential_helper exists \
    --host sip.linphone.org --username traveler-example --kind linphone-password)"
sudo_present="$($credential_helper exists \
    --host 192.168.50.10 --username gateway --kind sudo-password)"

printf 'KEYRING_LINPHONE=%s\n' "$linphone_present"
printf 'KEYRING_SUDO_192_168_1_128=%s\n' "$sudo_present"

