#!/usr/bin/python3
"""One-time migration of the three accepted rows from the 2026-11-14 incident.
Does not send messages; does not print sender/body/content digest.
Run only while the bridge is stopped. Keeps a private SQLite backup.
"""
import os,sys,sqlite3,json,time,datetime as dt
from pathlib import Path
os.umask(0o077)
os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path=/run/user/1000/bus'
sys.path.insert(0,str(Path.home()/'.local/lib/asterisk-sms-bridge'))
import bridge,dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
DBusGMainLoop(set_as_default=True)
state=Path.home()/'.local/state/asterisk-sms-bridge'
dbpath=state/'queue.sqlite3'
if not (state/'before-content-dedup.sqlite3').exists():
 with sqlite3.connect(dbpath) as src:
  with sqlite3.connect(state/'before-content-dedup.sqlite3') as backup:src.backup(backup)
store=bridge.Store(dbpath)
legacy=store.db.execute("SELECT id,stamp FROM messages WHERE status='accepted'").fetchall()
allowed={'24c934c936ae','640ade08cfce','9be1a987e568'}
legacy=[r for r in legacy if r[0][:12] in allowed]
config=json.loads((Path.home()/'.config/asterisk-sms-bridge/config.json').read_text())
bus=dbus.SessionBus();client=dbus.Interface(bus.get_object(bridge.OBEX,'/org/bluez/obex'),bridge.OBEX+'.Client1')
session=client.CreateSession(config['device'],{'Target':'map','Source':config['adapter']},timeout=25)
target=state/'migration.bmsg';seeded=set()
try:
 ma=dbus.Interface(bus.get_object(bridge.OBEX,session),bridge.OBEX+'.MessageAccess1')
 ma.SetFolder('telecom');ma.SetFolder('msg')
 rows=ma.ListMessages('inbox',{'MaxCount':dbus.UInt16(100),'SubjectLength':dbus.Byte(0),'Fields':dbus.Array(['timestamp','sender-address','type','size'],signature='s')},timeout=25)
 for path,meta in rows.items():
  stamp=str(meta.get('Timestamp',''))
  epoch=lambda s:dt.datetime.strptime(s,'%Y%m%dT%H%M%S').replace(tzinfo=dt.timezone.utc).timestamp()
  matches=[key for key,oldstamp in legacy if abs(epoch(stamp)-epoch(oldstamp))<=2]
  if not matches:continue
  msg=dbus.Interface(bus.get_object(bridge.OBEX,path),bridge.OBEX+'.Message1')
  target.unlink(missing_ok=True)
  transfer=None; outcome={}; loop=GLib.MainLoop()
  def changed(iface,props,invalid,path):
   if str(path)==str(transfer) and iface==bridge.OBEX+'.Transfer1' and props.get('Status') in ('complete','error'):
    outcome['status']=str(props['Status']);loop.quit()
  match=bus.add_signal_receiver(changed,signal_name='PropertiesChanged',dbus_interface='org.freedesktop.DBus.Properties',bus_name=bridge.OBEX,path_keyword='path')
  transfer,props=msg.Get(str(target),False,timeout=25)
  if props.get('Status') in ('complete','error'):outcome['status']=str(props['Status'])
  else:
   timer=GLib.timeout_add_seconds(30,lambda:(loop.quit(),False)[1])
   loop.run()
   if outcome:GLib.source_remove(timer)
  match.remove()
  if outcome.get('status')!='complete':raise RuntimeError('migration download did not complete')
  sender,body=bridge.parse_bmessage(target.read_bytes());sender=str(meta.get('SenderAddress','')) or sender or 'Unknown sender'
  with store.db:
   for key in matches:store.remember_identity(key,sender,stamp,body);seeded.add(key)
  target.unlink(missing_ok=True)
 assert len(seeded)==len(legacy), 'some legacy identities could not be recovered'
 print(json.dumps({'legacy_rows_seeded':len(seeded),'messages_sent':0,'private_content_printed':False}))
finally:
 target.unlink(missing_ok=True)
 client.RemoveSession(session)
 store.db.close()
