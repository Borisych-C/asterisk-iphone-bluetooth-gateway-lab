#!/usr/bin/env bash
set -euo pipefail

payload_dir="${1:-/tmp/asterisk-linphone-push-payload}"
backup_root="/var/backups/asterisk-linphone-push-auth"
stamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$backup_root/$stamp"
pjsip_target="/etc/asterisk/pjsip_linphone_push.conf"
auth_target="/etc/asterisk/pjsip_linphone_push_auth.conf"
deployment_complete=0
linphone_password=""
temp_auth=""

cleanup() {
    unset linphone_password
    if [[ -n "$temp_auth" && -f "$temp_auth" ]]; then
        rm -f "$temp_auth"
    fi
}

rollback() {
    local status=$?
    cleanup
    if [[ "$deployment_complete" -eq 1 || ! -d "$backup_dir" ]]; then
        exit "$status"
    fi

    printf 'Linphone auth deployment failed; restoring %s\n' "$backup_dir" >&2
    for target in /etc/asterisk/pjsip.conf "$pjsip_target" "$auth_target"; do
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
trap cleanup EXIT

if [[ "$EUID" -ne 0 ]]; then
    printf 'remote_install_auth.sh must run as root\n' >&2
    exit 1
fi

if ! IFS= read -r linphone_password || [[ -z "$linphone_password" ]]; then
    printf 'No Linphone password received.\n' >&2
    exit 1
fi

for required in \
    "$payload_dir/config/pjsip_linphone_push.conf" \
    "$payload_dir/config/pjsip_linphone_push_auth.conf.in"; do
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
for source in /etc/asterisk/pjsip.conf "$pjsip_target" "$auth_target"; do
    if [[ -e "$source" || -L "$source" ]]; then
        cp -a "$source" "$backup_dir/"
    fi
done

install -o asterisk -g asterisk -m 0640 \
    "$payload_dir/config/pjsip_linphone_push.conf" "$pjsip_target"

temp_auth="$(mktemp)"
chmod 0600 "$temp_auth"
while IFS= read -r line; do
    if [[ "$line" == 'password=__LINPHONE_PASSWORD__' ]]; then
        printf 'password=%s\n' "$linphone_password"
    else
        printf '%s\n' "$line"
    fi
done < "$payload_dir/config/pjsip_linphone_push_auth.conf.in" > "$temp_auth"
unset linphone_password
install -o asterisk -g asterisk -m 0640 "$temp_auth" "$auth_target"
rm -f "$temp_auth"
temp_auth=""

grep -qxF '#include pjsip_linphone_push_auth.conf' /etc/asterisk/pjsip.conf || \
    printf '\n#include pjsip_linphone_push_auth.conf\n' >> /etc/asterisk/pjsip.conf

asterisk -rx 'core reload'
sleep 2
asterisk -rx 'pjsip show endpoint linphone-push' | \
    grep -E 'Endpoint:|I/OAuth:|outbound_auth|from_user|from_domain|transport'
asterisk -rx 'pjsip show auth linphone-push-auth' | \
    grep -E 'Auth:|auth_type|realm|username'

deployment_complete=1
printf 'LINPHONE_AUTH_BACKUP=%s\n' "$backup_dir"
