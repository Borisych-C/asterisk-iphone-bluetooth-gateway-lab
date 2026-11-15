#!/usr/bin/env bash
set -euo pipefail

payload_dir="${1:-/tmp/asterisk-linphone-push-payload}"
source_file="$payload_dir/config/extensions_local.conf"
target_file="/etc/asterisk/extensions_local.conf"
backup_root="/var/backups/asterisk-linphone-push-incoming"
stamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$backup_root/$stamp"
expected_old_sha="913e9964553cb209b60dc62bdcc486c4581acb8c4d9b06b0cabb3fab3c0727de"
deployment_complete=0

rollback() {
    local status=$?
    if [[ "$deployment_complete" -eq 1 || ! -f "$backup_dir/extensions_local.conf" ]]; then
        exit "$status"
    fi
    printf 'Incoming-route deployment failed; restoring %s\n' "$backup_dir" >&2
    cp -a "$backup_dir/extensions_local.conf" "$target_file"
    asterisk -rx 'dialplan reload' >/dev/null 2>&1 || true
    exit "$status"
}

trap rollback ERR

if [[ "$EUID" -ne 0 ]]; then
    printf 'remote_switch_incoming.sh must run as root\n' >&2
    exit 1
fi
if [[ ! -f "$source_file" ]]; then
    printf 'Missing payload file: %s\n' "$source_file" >&2
    exit 1
fi
if ! asterisk -rx 'core show channels count' | grep -Eq '^0 active call'; then
    printf 'Asterisk has an active call or channel; deployment aborted.\n' >&2
    asterisk -rx 'core show channels count' >&2 || true
    exit 1
fi

current_sha="$(sha256sum "$target_file" | awk '{print $1}')"
if [[ "$current_sha" != "$expected_old_sha" ]]; then
    printf 'Live extensions_local.conf changed unexpectedly (%s); refusing overwrite.\n' \
        "$current_sha" >&2
    exit 1
fi

install -d -m 0700 "$backup_dir"
cp -a "$target_file" "$backup_dir/extensions_local.conf"
install -o root -g root -m 0644 "$source_file" "$target_file"

asterisk -rx 'dialplan reload'
asterisk -rx 'dialplan show s@from-home-mobile' | \
    grep -E "'s'|NoOp|Dial|Hangup|extension"

deployment_complete=1
printf 'LINPHONE_INCOMING_BACKUP=%s\n' "$backup_dir"

