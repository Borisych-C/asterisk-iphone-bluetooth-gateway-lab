#!/usr/bin/env bash
set -euo pipefail

payload_dir="${1:-/tmp/asterisk-pwa-vpn-hairpin-payload}"
script_source="$payload_dir/asterisk-pwa-hairpin"
cron_source="$payload_dir/asterisk-pwa-hairpin.cron"
script_target="/usr/local/sbin/asterisk-pwa-hairpin"
cron_target="/etc/cron.d/asterisk-pwa-hairpin"
backup_root="/var/backups/asterisk-pwa-vpn-hairpin"
stamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$backup_root/$stamp"
deployment_complete=0

if [[ "$EUID" -ne 0 ]]; then
    printf 'remote_install.sh must run as root\n' >&2
    exit 1
fi

for required in "$script_source" "$cron_source"; do
    if [[ ! -f "$required" ]]; then
        printf 'Missing payload file: %s\n' "$required" >&2
        exit 1
    fi
done

install -d -m 0700 "$backup_dir"
for source in "$script_target" "$cron_target"; do
    if [[ -e "$source" ]]; then
        cp -a "$source" "$backup_dir/"
    fi
done
/usr/sbin/nft list table ip asterisk_pwa_hairpin \
    > "$backup_dir/nft-table-before.txt" 2>/dev/null || true

rollback() {
    local status=$?
    if [[ "$deployment_complete" -eq 1 ]]; then
        exit "$status"
    fi

    printf 'PWA hairpin deployment failed; restoring from %s\n' "$backup_dir" >&2
    /usr/sbin/nft delete table ip asterisk_pwa_hairpin >/dev/null 2>&1 || true
    for target in "$script_target" "$cron_target"; do
        local saved="$backup_dir/$(basename "$target")"
        if [[ -e "$saved" ]]; then
            cp -a "$saved" "$target"
        else
            rm -f "$target"
        fi
    done
    if [[ -x "$script_target" ]]; then
        "$script_target" >/dev/null 2>&1 || true
    fi
    exit "$status"
}
trap rollback ERR

install -o root -g root -m 0755 "$script_source" "$script_target"
install -o root -g root -m 0644 "$cron_source" "$cron_target"
rm -f /run/asterisk-pwa-hairpin-wan
"$script_target"

/usr/sbin/nft -a list table ip asterisk_pwa_hairpin
grep -qxF '@reboot root sleep 20; /usr/local/sbin/asterisk-pwa-hairpin' "$cron_target"
grep -qxF '*/2 * * * * root /usr/local/sbin/asterisk-pwa-hairpin' "$cron_target"

deployment_complete=1
printf 'PWA_HAIRPIN_BACKUP=%s\n' "$backup_dir"
printf 'PWA_HAIRPIN_WAN=%s\n' "$(cat /run/asterisk-pwa-hairpin-wan)"
printf 'PWA_HAIRPIN_TARGET=192.168.50.10:443\n'
