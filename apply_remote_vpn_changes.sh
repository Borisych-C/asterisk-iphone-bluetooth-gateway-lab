#!/usr/bin/env bash
set -euo pipefail

remote_host="192.168.50.20"
remote_payload="/tmp/asterisk-pwa-vpn-dns-payload"
profile_dir="/home/gateway/vpn"

rsync -a --delete ./stage1/vpn-dns/ "$remote_host:$remote_payload/"

sudo_password="$(zenity --password --title='Stage 1: configure VPN split DNS')"
trap 'unset sudo_password' EXIT

printf '%s\n' "$sudo_password" | ssh -o BatchMode=yes "$remote_host" \
    "sudo -S -p '' '$remote_payload/remote_install.sh' '$remote_payload'"

for profile_name in iphone-amneziawg iphone-amneziawg-full; do
    profile_source="$profile_dir/$profile_name.conf"
    profile_target="$profile_dir/$profile_name-split-dns.conf"
    if [[ -e "$profile_target" ]]; then
        cp -a "$profile_target" "$profile_target.bak-$(date +%Y%m%d-%H%M%S)"
    fi
    cp -a "$profile_source" "$profile_target"
    sed -i -E 's|^DNS[[:space:]]*=.*$|DNS = 10.77.77.1|' "$profile_target"
    chmod 0600 "$profile_target"

    printf 'UPDATED_PROFILE=%s\n' "$profile_target"
    grep -E '^(Address|DNS|Endpoint|AllowedIPs|PersistentKeepalive)[[:space:]]*=' "$profile_target"
done
