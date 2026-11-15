#!/usr/bin/env bash
set -euo pipefail

if [[ "$EUID" -ne 0 ]]; then
    printf 'run_verify_credentials.sh must run as root\n' >&2
    exit 1
fi

auth_file="/etc/asterisk/pjsip_linphone_push_auth.conf"
curl_config="$(mktemp)"
trap 'rm -f "$curl_config"; unset linphone_password escaped_password' EXIT
chmod 0600 "$curl_config"

linphone_password="$(sed -n 's/^password=//p' "$auth_file" | head -1)"
if [[ -z "$linphone_password" ]]; then
    printf 'Stored Linphone password is missing.\n' >&2
    exit 1
fi

escaped_password="${linphone_password//\\/\\\\}"
escaped_password="${escaped_password//\"/\\\"}"
printf 'user = "traveler-example:%s"\n' "$escaped_password" > "$curl_config"
unset linphone_password escaped_password

http_code="$(curl --config "$curl_config" --digest --silent --show-error \
    --output /dev/null --write-out '%{http_code}' \
    --header 'Accept: application/json' \
    --header 'Content-Type: application/json' \
    'https://subscribe.linphone.org/api/accounts/me')"

printf 'LINPHONE_ACCOUNT_API_HTTP=%s\n' "$http_code"
if [[ "$http_code" != 200 ]]; then
    exit 2
fi

