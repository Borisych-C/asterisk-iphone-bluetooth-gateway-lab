#!/usr/bin/env bash
set -euo pipefail

remote_host="192.168.50.20"
remote_payload="/tmp/asterisk-pwa-vpn-hairpin-payload"

rsync -a --delete ./stage1/vpn-hairpin/ "$remote_host:$remote_payload/"

sudo_password="$(zenity --password --title='Stage 1: configure VPN HTTPS hairpin')"
trap 'unset sudo_password' EXIT

printf '%s\n' "$sudo_password" | ssh -o BatchMode=yes "$remote_host" \
    "sudo -S -p '' '$remote_payload/remote_install.sh' '$remote_payload'"
