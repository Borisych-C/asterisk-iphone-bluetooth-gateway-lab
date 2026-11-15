#!/usr/bin/env bash
set -euo pipefail

payload_dir="${1:-/tmp/asterisk-pwa-vpn-dns-payload}"
config_source="$payload_dir/asterisk-pwa-vpn.conf"
config_target="/etc/dnsmasq.d/asterisk-pwa-vpn.conf"
backup_root="/var/backups/asterisk-pwa-vpn-dns"
stamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$backup_root/$stamp"
package_was_installed=0
deployment_complete=0

if [[ "$EUID" -ne 0 ]]; then
    printf 'remote_install.sh must run as root\n' >&2
    exit 1
fi

if [[ ! -f "$config_source" ]]; then
    printf 'Missing payload file: %s\n' "$config_source" >&2
    exit 1
fi

if dpkg-query -W -f='${Status}\n' dnsmasq 2>/dev/null | grep -qxF 'install ok installed'; then
    package_was_installed=1
fi

install -d -m 0700 "$backup_dir"
if [[ -e "$config_target" ]]; then
    cp -a "$config_target" "$backup_dir/"
fi
if command -v nft >/dev/null 2>&1; then
    nft list ruleset > "$backup_dir/nftables-before.txt" 2>/dev/null || true
elif [[ -x /usr/sbin/nft ]]; then
    /usr/sbin/nft list ruleset > "$backup_dir/nftables-before.txt" 2>/dev/null || true
fi

rollback() {
    local status=$?
    if [[ "$deployment_complete" -eq 1 ]]; then
        exit "$status"
    fi

    printf 'VPN DNS deployment failed; restoring previous configuration from %s\n' "$backup_dir" >&2
    if [[ -f "$backup_dir/asterisk-pwa-vpn.conf" ]]; then
        cp -a "$backup_dir/asterisk-pwa-vpn.conf" "$config_target"
        service dnsmasq restart >/dev/null 2>&1 || true
    else
        rm -f "$config_target"
        if [[ "$package_was_installed" -eq 0 ]]; then
            service dnsmasq stop >/dev/null 2>&1 || true
        else
            service dnsmasq restart >/dev/null 2>&1 || true
        fi
    fi
    exit "$status"
}
trap rollback ERR

install -d -m 0755 /etc/dnsmasq.d
install -o root -g root -m 0644 "$config_source" "$config_target"

if [[ "$package_was_installed" -eq 0 ]]; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get install -y dnsmasq
fi

dnsmasq --test
service dnsmasq restart
sleep 2
service dnsmasq status

listener_output="$(ss -lnutp | grep -E '10\.77\.77\.1:53([[:space:]]|$)' || true)"
if [[ -z "$listener_output" ]]; then
    printf 'dnsmasq is not listening on 10.77.77.1:53\n' >&2
    ss -lnutp | grep -E '(:53[[:space:]])' >&2 || true
    exit 1
fi
printf '%s\n' "$listener_output"

target_answer="$(busybox nslookup home.example.net 10.77.77.1 2>&1)"
printf '%s\n' "$target_answer"
grep -q '192.168.50.10' <<<"$target_answer"

target_aaaa_answer="$(busybox nslookup -type=AAAA home.example.net 10.77.77.1 2>&1 || true)"
printf '%s\n' "$target_aaaa_answer"
if grep -Eq 'Address: ([[:xdigit:]]+:){2,}' <<<"$target_aaaa_answer"; then
    printf 'Public IPv6 answer leaked through split DNS\n' >&2
    exit 1
fi

forward_answer="$(busybox nslookup www.debian.org 10.77.77.1 2>&1)"
printf '%s\n' "$forward_answer"
grep -q '^Address:' <<<"$forward_answer"

curl --fail --silent --show-error --resolve \
    home.example.net:443:192.168.50.10 \
    -o /dev/null \
    https://home.example.net/flacmusic/phone-probe/

deployment_complete=1
printf 'VPN_DNS_BACKUP=%s\n' "$backup_dir"
printf 'VPN_DNS_SERVER=10.77.77.1\n'
printf 'VPN_DNS_RECORD=home.example.net -> 192.168.50.10\n'
