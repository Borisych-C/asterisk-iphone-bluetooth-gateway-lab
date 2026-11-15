#!/usr/bin/env bash
set -euo pipefail
umask 077

# Credentials stay on the server and are never passed in curl's command line.
source "${DUCKDNS_CONFIG:-/etc/duckdns-ip-update.conf}"
STATE_FILE="${DUCKDNS_STATE_FILE:-/var/lib/duckdns-ip-update/last_ipv6}"
LOCK_FILE="${DUCKDNS_LOCK_FILE:-/var/lib/duckdns-ip-update/lock}"

log() { printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"; }
[[ ${DOMAIN:-} =~ ^[A-Za-z0-9,-]+$ && ${TOKEN:-} =~ ^[A-Za-z0-9-]+$ ]] || {
  log 'DuckDNS=FAIL stage=config reason=invalid-settings'; exit 1;
}
exec 9>"$LOCK_FILE"
flock -n 9 || { log 'DuckDNS=SKIP reason=already-running'; exit 0; }

valid_ipv4() {
  local value=$1 octet
  [[ $value =~ ^[0-9]{1,3}(\.[0-9]{1,3}){3}$ ]] || return 1
  local -a octets
  IFS=. read -r -a octets <<< "$value"
  for octet in "${octets[@]}"; do ((10#$octet <= 255)) || return 1; done
}

fetch() {
  local stage=$1 url=$2 expected=$3 attempt result rc http body reason retry
  for attempt in 1 2 3; do
    rc=0
    result="$(printf 'url = "%s"\n' "$url" | curl -q -4 --silent \
      --connect-timeout 5 --max-time 15 --max-filesize 4096 \
      --write-out $'\n%{http_code}' --config - 2>/dev/null)" || rc=$?
    http=${result##*$'\n'}
    body=${result%$'\n'*}
    body=${body//$'\r'/}
    body=${body//$'\n'/}
    reason=http-error
    retry=0
    if ((rc == 0)) && [[ $http == 200 ]]; then
      if { [[ $expected == ipv4 ]] && valid_ipv4 "$body"; } || \
         { [[ $expected == duckdns ]] && [[ $body == OK ]]; }; then
        FETCH_BODY=$body
        if ((attempt > 1)); then log "DuckDNS=RECOVERED stage=$stage attempt=$attempt"; fi
        return 0
      fi
      reason=invalid-response
      [[ $body == KO ]] && reason=api-rejected
    else
      case "$rc:$http" in
        0:408|0:429|0:500|0:502|0:503|0:504|6:*|7:*|18:*|28:*|35:*|52:*|55:*|56:*) retry=1 ;;
      esac
    fi
    log "DuckDNS=RETRY_ERROR stage=$stage attempt=$attempt/3 curl=$rc http=$http reason=$reason"
    if ((retry == 0 || attempt == 3)); then
      log "DuckDNS=FAIL stage=$stage attempts=$attempt reason=$reason"
      return 1
    fi
    sleep "$((attempt * 2))"
  done
}

fetch public-ip 'https://checkip.amazonaws.com' ipv4 || exit 1
IP4=$FETCH_BODY
if ! IP6="$(ip -6 -o addr show dev "${IPV6_IF:-enp4s0}" scope global up \
  | awk '$4 ~ /^[23][[:xdigit:]][[:xdigit:]][[:xdigit:]]:/ && !/(^|[[:space:]])(temporary|deprecated|tentative|dadfailed)([[:space:]]|$)/ {split($4, a, "/"); print a[1]; exit}')"; then
  log 'DuckDNS=FAIL stage=local-ipv6 reason=address-query-failed'; exit 1
fi
[[ -z $IP6 || $IP6 =~ ^[[:xdigit:]:]+$ ]] || {
  log 'DuckDNS=FAIL stage=local-ipv6 reason=invalid-address'; exit 1;
}
BASE_URL="https://www.duckdns.org/update?domains=${DOMAIN}&token=${TOKEN}"
clear_ok=1
if [[ -n $IP6 ]]; then
  fetch update "${BASE_URL}&ip=${IP4}&ipv6=${IP6}" duckdns || exit 1
  IP6_LOG=$IP6
else
  if [[ ! -e $STATE_FILE || -s $STATE_FILE ]]; then
    fetch clear-ipv6 "${BASE_URL}&clear=true" duckdns || clear_ok=0
  fi
  # A failed clear may nevertheless have reached the server. Always restore A.
  fetch update "${BASE_URL}&ip=${IP4}" duckdns || exit 1
  IP6_LOG=none
fi
if ((clear_ok == 0)); then
  log "IPv4=${IP4} DuckDNS=FAIL stage=clear-ipv6 reason=cleanup-unconfirmed-ipv4-updated"
  exit 1
fi
state_tmp="$(mktemp "$(dirname "$STATE_FILE")/.duckdns-state.XXXXXX")"
trap 'rm -f -- "${state_tmp:-}"' EXIT
if [[ -n $IP6 ]]; then printf '%s\n' "$IP6" >"$state_tmp"; else : >"$state_tmp"; fi
mv -f -- "$state_tmp" "$STATE_FILE"
state_tmp=''
log "IPv4=${IP4} IPv6=${IP6_LOG} DuckDNS=OK"
