#!/usr/bin/env bash
set -euo pipefail

payload_dir="${1:-/tmp/asterisk-pwa-stage1-payload}"
backup_root="/var/backups/asterisk-pwa-stage1"
stamp="$(date +%Y%m%d-%H%M%S)"
backup_dir="$backup_root/$stamp"
release_dir="/var/www/asterisk-pwa-stage1-$stamp"
web_link="/var/www/asterisk-pwa-stage1"
apache_conf="/etc/apache2/conf-available/asterisk-pwa-stage1.conf"
pjsip_stage_conf="/etc/asterisk/pjsip_stage1.conf"
extensions_stage_conf="/etc/asterisk/extensions_stage1.conf"
deployment_complete=0
apache_was_enabled=0

if [[ -L /etc/apache2/conf-enabled/asterisk-pwa-stage1.conf ]]; then
    apache_was_enabled=1
fi

rollback() {
    local status=$?
    if [[ "$deployment_complete" -eq 1 || ! -d "$backup_dir" ]]; then
        exit "$status"
    fi

    printf 'Stage 1 deployment failed; restoring protected configuration from %s\n' "$backup_dir" >&2
    for target in \
        /etc/asterisk/http.conf \
        /etc/asterisk/pjsip.conf \
        /etc/asterisk/extensions.conf \
        "$pjsip_stage_conf" \
        "$extensions_stage_conf" \
        "$apache_conf"; do
        local saved="$backup_dir/$(basename "$target")"
        if [[ -e "$saved" || -L "$saved" ]]; then
            cp -a "$saved" "$target"
        else
            rm -f "$target"
        fi
    done

    if [[ -f "$backup_dir/previous-web-link" ]]; then
        ln -sfn "$(cat "$backup_dir/previous-web-link")" "$web_link"
    elif [[ -L "$web_link" ]]; then
        unlink "$web_link"
    fi

    if [[ "$apache_was_enabled" -eq 0 ]]; then
        a2disconf asterisk-pwa-stage1 >/dev/null 2>&1 || true
    fi
    apache2ctl configtest >/dev/null 2>&1 && systemctl reload apache2 || true
    systemctl restart asterisk || true
    exit "$status"
}

trap rollback ERR

if [[ "$EUID" -ne 0 ]]; then
    printf 'remote_install.sh must run as root\n' >&2
    exit 1
fi

for required in \
    "$payload_dir/browser-phone/index.html" \
    "$payload_dir/browser-phone/stage1-runtime.js" \
    "$payload_dir/config/pjsip_stage1.conf" \
    "$payload_dir/config/extensions_stage1.conf" \
    "$payload_dir/config/asterisk-pwa-stage1-apache.conf"; do
    if [[ ! -f "$required" ]]; then
        printf 'Missing payload file: %s\n' "$required" >&2
        exit 1
    fi
done

if ! asterisk -rx 'core show channels count' | grep -Eq '^0 active call'; then
    printf 'Asterisk has an active call or channel; deployment aborted before changes.\n' >&2
    asterisk -rx 'core show channels count' >&2 || true
    exit 1
fi

install -d -m 0700 "$backup_dir"
for source in \
    /etc/asterisk/http.conf \
    /etc/asterisk/pjsip.conf \
    /etc/asterisk/extensions.conf \
    "$pjsip_stage_conf" \
    "$extensions_stage_conf" \
    "$apache_conf"; do
    if [[ -e "$source" || -L "$source" ]]; then
        cp -a "$source" "$backup_dir/"
    fi
done
if [[ -L "$web_link" ]]; then
    readlink "$web_link" > "$backup_dir/previous-web-link"
elif [[ -e "$web_link" ]]; then
    printf '%s exists and is not a symlink; refusing to replace it.\n' "$web_link" >&2
    exit 1
fi

existing_secret=""
if [[ -f "$pjsip_stage_conf" ]]; then
    existing_secret="$(sed -n 's/^password=\([[:xdigit:]]\{48\}\)$/\1/p' "$pjsip_stage_conf" | head -1)"
fi
if [[ -n "$existing_secret" ]]; then
    sip_secret="$existing_secret"
else
    sip_secret="$(openssl rand -hex 24)"
fi

install -d -m 0755 "$release_dir"
cp -a "$payload_dir/browser-phone/." "$release_dir/"
sed -i "s/__PWA_STAGE1_PASSWORD__/$sip_secret/g" "$release_dir/stage1-runtime.js"
chown -R root:root "$release_dir"
find "$release_dir" -type d -exec chmod 0755 {} +
find "$release_dir" -type f -exec chmod 0644 {} +
chown root:www-data "$release_dir/stage1-runtime.js"
chmod 0640 "$release_dir/stage1-runtime.js"

install -o asterisk -g asterisk -m 0640 "$payload_dir/config/pjsip_stage1.conf" "$pjsip_stage_conf"
sed -i "s/__PWA_STAGE1_PASSWORD__/$sip_secret/g" "$pjsip_stage_conf"
install -o asterisk -g asterisk -m 0640 "$payload_dir/config/extensions_stage1.conf" "$extensions_stage_conf"
install -o root -g root -m 0644 "$payload_dir/config/asterisk-pwa-stage1-apache.conf" "$apache_conf"

grep -qxF '#include pjsip_stage1.conf' /etc/asterisk/pjsip.conf || \
    printf '\n#include pjsip_stage1.conf\n' >> /etc/asterisk/pjsip.conf
grep -qxF '#include extensions_stage1.conf' /etc/asterisk/extensions.conf || \
    printf '\n#include extensions_stage1.conf\n' >> /etc/asterisk/extensions.conf

sed -i -E 's/^[;[:space:]]*enabled=yes[[:space:]]*$/enabled=yes/' /etc/asterisk/http.conf
sed -i -E 's/^[;[:space:]]*bindport=8088[[:space:]]*$/bindport=8088/' /etc/asterisk/http.conf
grep -qxF 'enabled=yes' /etc/asterisk/http.conf
grep -qxF 'bindaddr=127.0.0.1' /etc/asterisk/http.conf
grep -qxF 'bindport=8088' /etc/asterisk/http.conf

ln -sfn "$release_dir" "$web_link"
a2enconf asterisk-pwa-stage1 >/dev/null

apache2ctl configtest

systemctl reload apache2
systemctl restart asterisk
sleep 4

systemctl is-active --quiet apache2
systemctl is-active --quiet asterisk
asterisk -rx 'http show status'
asterisk -rx 'pjsip show transport transport-wss-stage1'
asterisk -rx 'pjsip show endpoint 1099'
asterisk -rx 'dialplan show from-pwa-stage1'
asterisk -rx 'mobile show devices'

deployment_complete=1
printf 'STAGE1_RELEASE=%s\n' "$release_dir"
printf 'STAGE1_BACKUP=%s\n' "$backup_dir"
printf 'STAGE1_URL=https://home.example.net/flacmusic/phone-probe/\n'
