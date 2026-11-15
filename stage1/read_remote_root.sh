#!/usr/bin/env bash
set -euo pipefail

remote_host="192.168.50.10"
sudo_password="$(zenity --password --title='Stage 1: read Asterisk configuration')"
trap 'unset sudo_password' EXIT

printf '%s\n' "$sudo_password" | ssh -o BatchMode=yes "$remote_host" \
  "sudo -S -p '' sh -c 'for file in /etc/asterisk/http.conf /etc/asterisk/pjsip.conf /etc/asterisk/extensions.conf; do printf \"===%s includes/tail===\\n\" \"\$file\"; grep -nE \"^[[:space:]]*#include|^[[:space:]]*enabled=|^[[:space:]]*bindaddr=|^[[:space:]]*bindport=\" \"\$file\" || true; tail -50 \"\$file\"; done'"
