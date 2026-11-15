#!/bin/sh
# Run on the target server as gateway. Does not restart Asterisk or Bluetooth.
set -eu
cd -- "$(dirname -- "$0")"
python3 -c 'import dbus, gi, sqlite3, ssl; from zoneinfo import ZoneInfo; ZoneInfo("Asia/Jerusalem")'
python3 -m unittest discover -s tests
install -d -m 700 "$HOME/.local/lib/asterisk-sms-bridge" "$HOME/.config/asterisk-sms-bridge" "$HOME/.local/state/asterisk-sms-bridge" "$HOME/.config/systemd/user"
# A previous program/config is retained; the database is NEVER replaced.
for file in "$HOME/.local/lib/asterisk-sms-bridge/bridge.py" "$HOME/.local/lib/asterisk-sms-bridge/outgoing.py" "$HOME/.config/asterisk-sms-bridge/config.json" "$HOME/.config/systemd/user/asterisk-sms-bridge.service"; do
    if [ -f "$file" ]; then cp -p "$file" "$file.previous"; fi
done
install -m 600 outgoing.py "$HOME/.local/lib/asterisk-sms-bridge/outgoing.py"
install -m 600 bridge.py "$HOME/.local/lib/asterisk-sms-bridge/bridge.py"
install -m 600 config.json "$HOME/.config/asterisk-sms-bridge/config.json"
install -m 600 systemd/asterisk-sms-bridge.service "$HOME/.config/systemd/user/asterisk-sms-bridge.service"
python3 - <<'PYCONFIG'
import json,pwd
from pathlib import Path
p=Path.home()/'.config/asterisk-sms-bridge/config.json'
v=json.loads(p.read_text());v['submit_uid']=pwd.getpwnam('asterisk').pw_uid
p.write_text(json.dumps(v,indent=2)+'\n')
assert Path(v['submit_socket']).parent.is_dir(), 'Run asterisk/install-root.py as administrator first'
PYCONFIG
systemctl --user daemon-reload
systemctl --user enable asterisk-sms-bridge.service
systemctl --user restart asterisk-sms-bridge.service
systemctl --user is-active asterisk-sms-bridge.service
