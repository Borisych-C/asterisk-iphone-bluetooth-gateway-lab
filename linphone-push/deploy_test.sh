#!/usr/bin/env bash
set -euo pipefail

remote_host="192.168.50.10"
remote_payload="/tmp/asterisk-linphone-push-payload"

rsync -a --delete ./linphone-push/ "$remote_host:$remote_payload/"

sudo_password="$(zenity --password --title='Install Linphone push test route')"
trap 'unset sudo_password' EXIT

printf '%s\n' "$sudo_password" | ssh -o BatchMode=yes "$remote_host" \
    "sudo -S -p '' '$remote_payload/remote_install_test.sh' '$remote_payload'"

