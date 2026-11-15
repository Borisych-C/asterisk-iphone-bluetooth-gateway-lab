#!/usr/bin/env bash
set -euo pipefail

domain="home-example"
fqdn="${domain}.duckdns.org"
token_source="/home/gateway/HA/update_duckdns.sh"
backup_root="/var/backups/asterisk-pwa-duckdns"
stamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$backup_root/$stamp"
completed=0

if [[ "$EUID" -ne 0 ]]; then
    printf 'clear_stale_duckdns_aaaa.sh must run as root\n' >&2
    exit 1
fi

token_value="$(sed -n 's/^TOKEN=//p' "$token_source" | head -1)"
token_value="${token_value%\"}"
token_value="${token_value#\"}"
token_value="${token_value%\'}"
token_value="${token_value#\'}"
if [[ -z "$token_value" ]]; then
    printf 'Could not read DuckDNS account token from %s\n' "$token_source" >&2
    exit 1
fi

old_ipv4="$(getent ahostsv4 "$fqdn" | awk 'NR == 1 { print $1 }')"
old_ipv6="$(getent ahostsv6 "$fqdn" | awk 'NR == 1 { print $1 }')"
if [[ -z "$old_ipv4" ]]; then
    printf 'No current IPv4 record for %s\n' "$fqdn" >&2
    exit 1
fi

install -d -m 0700 "$backup_dir"
{
    printf 'FQDN=%s\n' "$fqdn"
    printf 'IPV4=%s\n' "$old_ipv4"
    printf 'IPV6=%s\n' "$old_ipv6"
} > "$backup_dir/records-before.txt"
chmod 0600 "$backup_dir/records-before.txt"

restore_records() {
    local status=$?
    if [[ "$completed" -eq 1 ]]; then
        exit "$status"
    fi
    printf 'DuckDNS update failed; restoring previous records\n' >&2
    curl -fsS --max-time 15 \
        "https://www.duckdns.org/update?domains=${domain}&token=${token_value}&ip=${old_ipv4}&ipv6=${old_ipv6}" \
        >/dev/null 2>&1 || true
    exit "$status"
}
trap restore_records ERR

clear_response="$(curl -fsS --max-time 15 \
    "https://www.duckdns.org/update?domains=${domain}&token=${token_value}&clear=true")"
if [[ "$clear_response" != "OK" ]]; then
    printf 'DuckDNS clear returned: %s\n' "$clear_response" >&2
    false
fi

ipv4_response="$(curl -fsS --max-time 15 \
    "https://www.duckdns.org/update?domains=${domain}&token=${token_value}&ip=${old_ipv4}")"
if [[ "$ipv4_response" != "OK" ]]; then
    printf 'DuckDNS IPv4 restore returned: %s\n' "$ipv4_response" >&2
    false
fi

completed=1
printf 'DUCKDNS_BACKUP=%s\n' "$backup_dir"
printf 'DUCKDNS_FQDN=%s\n' "$fqdn"
printf 'DUCKDNS_IPV4=%s\n' "$old_ipv4"
printf 'DUCKDNS_IPV6=cleared\n'
