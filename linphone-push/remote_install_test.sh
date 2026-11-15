#!/usr/bin/env bash
set -euo pipefail

payload_dir="${1:-/tmp/asterisk-linphone-push-payload}"
backup_root="/var/backups/asterisk-linphone-push"
stamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$backup_root/$stamp"
pjsip_target="/etc/asterisk/pjsip_linphone_push.conf"
extensions_target="/etc/asterisk/extensions_linphone_push.conf"
deployment_complete=0

rollback() {
    local status=$?
    if [[ "$deployment_complete" -eq 1 || ! -d "$backup_dir" ]]; then
        exit "$status"
    fi

    printf 'Linphone test-route deployment failed; restoring %s\n' "$backup_dir" >&2
    for target in \
        /etc/asterisk/pjsip.conf \
        /etc/asterisk/extensions.conf \
        "$pjsip_target" \
        "$extensions_target"; do
        local saved="$backup_dir/$(basename "$target")"
        if [[ -e "$saved" || -L "$saved" ]]; then
            cp -a "$saved" "$target"
        else
            rm -f "$target"
        fi
    done
    asterisk -rx 'core reload' >/dev/null 2>&1 || true
    exit "$status"
}

trap rollback ERR

if [[ "$EUID" -ne 0 ]]; then
    printf 'remote_install_test.sh must run as root\n' >&2
    exit 1
fi

for required in \
    "$payload_dir/config/pjsip_linphone_push.conf" \
    "$payload_dir/config/extensions_linphone_push.conf"; do
    if [[ ! -f "$required" ]]; then
        printf 'Missing payload file: %s\n' "$required" >&2
        exit 1
    fi
done

if ! asterisk -rx 'core show channels count' | grep -Eq '^0 active call'; then
    printf 'Asterisk has an active call or channel; deployment aborted.\n' >&2
    asterisk -rx 'core show channels count' >&2 || true
    exit 1
fi

install -d -m 0700 "$backup_dir"
for source in \
    /etc/asterisk/pjsip.conf \
    /etc/asterisk/extensions.conf \
    "$pjsip_target" \
    "$extensions_target"; do
    if [[ -e "$source" || -L "$source" ]]; then
        cp -a "$source" "$backup_dir/"
    fi
done

install -o asterisk -g asterisk -m 0640 \
    "$payload_dir/config/pjsip_linphone_push.conf" "$pjsip_target"
install -o asterisk -g asterisk -m 0640 \
    "$payload_dir/config/extensions_linphone_push.conf" "$extensions_target"

grep -qxF '#include pjsip_linphone_push.conf' /etc/asterisk/pjsip.conf || \
    printf '\n#include pjsip_linphone_push.conf\n' >> /etc/asterisk/pjsip.conf
grep -qxF '#include extensions_linphone_push.conf' /etc/asterisk/extensions.conf || \
    printf '\n#include extensions_linphone_push.conf\n' >> /etc/asterisk/extensions.conf

asterisk -rx 'core reload'
sleep 2
asterisk -rx 'pjsip show endpoint linphone-push'
asterisk -rx 'dialplan show 612@from-linphone-local'
asterisk -rx 'mobile show devices'

deployment_complete=1
printf 'LINPHONE_TEST_BACKUP=%s\n' "$backup_dir"

