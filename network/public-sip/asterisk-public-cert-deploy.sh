#!/bin/bash
set -euo pipefail
umask 077

lineage=/etc/letsencrypt/live/home.example.net
[[ ${RENEWED_LINEAGE:-$lineage} == "$lineage" ]] || exit 0
[[ $EUID == 0 ]] || { echo 'Run certificate deployment as root' >&2; exit 1; }
exec 9>/run/lock/asterisk-public-cert.lock
flock -w 30 9

openssl x509 -in "$lineage/fullchain.pem" -noout -checkend 86400 >/dev/null
openssl x509 -in "$lineage/fullchain.pem" -noout -checkhost home.example.net >/dev/null
cert_pub=$(openssl x509 -in "$lineage/fullchain.pem" -pubkey -noout | openssl pkey -pubin -outform DER | sha256sum)
key_pub=$(openssl pkey -in "$lineage/privkey.pem" -pubout -outform DER | sha256sum)
[[ $cert_pub == "$key_pub" ]] || { echo 'Certificate and private key do not match' >&2; exit 1; }

dest=/etc/asterisk/keys/public-sip
install -d -o root -g asterisk -m 0750 "$dest"
if cmp -s "$lineage/fullchain.pem" "$dest/fullchain.pem" && cmp -s "$lineage/privkey.pem" "$dest/privkey.pem"; then
    exit 0
fi
temp=$(mktemp -d "$dest/.renew.XXXXXX")
trap 'rm -rf -- "$temp"' EXIT
install -o root -g asterisk -m 0640 "$lineage/fullchain.pem" "$temp/fullchain.pem"
install -o root -g asterisk -m 0640 "$lineage/privkey.pem" "$temp/privkey.pem"
mv -f -- "$temp/fullchain.pem" "$dest/fullchain.pem"
mv -f -- "$temp/privkey.pem" "$dest/privkey.pem"
if [[ ${1:-} != --no-reload ]] && systemctl is-active --quiet asterisk.service; then
    /usr/sbin/asterisk -rx 'module reload res_pjsip.so'
fi
