#!/usr/bin/python3
"""Single explicitly requested outgoing test. Never retries PushMessage."""
import argparse,os,json,re,tempfile,time
from pathlib import Path
import dbus
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
p=argparse.ArgumentParser();p.add_argument('--recipient',required=True);p.add_argument('--send',action='store_true');p.add_argument('--originator-card',action='store_true');args=p.parse_args()
if not re.fullmatch(r'\+972[0-9]{9}',args.recipient):raise SystemExit('expected an Israeli mobile number')
if not args.send:raise SystemExit('--send required')
os.umask(0o077);os.environ['DBUS_SESSION_BUS_ADDRESS']='unix:path=/run/user/1000/bus'
DBusGMainLoop(set_as_default=True)
bus=dbus.SessionBus();service='org.bluez.obex'
objects=dbus.Interface(bus.get_object(service,'/'),'org.freedesktop.DBus.ObjectManager').GetManagedObjects()
sessions=[str(path) for path,ifs in objects.items() if service+'.MessageAccess1' in ifs]
if len(sessions)!=1:raise SystemExit('expected exactly one existing MAP session')
text='Home SIM test 2: new message via Asterisk gateway.'
part=('BEGIN:MSG\r\n'+text+'\r\nEND:MSG\r\n').encode('utf-8')
originator=('BEGIN:VCARD\r\nVERSION:2.1\r\nN:;;;;\r\nTEL:\r\nEND:VCARD\r\n') if args.originator_card else ''
data=('BEGIN:BMSG\r\nVERSION:1.0\r\nSTATUS:UNREAD\r\nTYPE:SMS_GSM\r\nFOLDER:telecom/msg/outbox\r\n'+originator+
      'BEGIN:BENV\r\nBEGIN:VCARD\r\nVERSION:2.1\r\nN:\r\nTEL:'+args.recipient+'\r\nEND:VCARD\r\n'
      'BEGIN:BBODY\r\nCHARSET:UTF-8\r\nLENGTH:'+str(len(part))+'\r\n').encode()+part+b'END:BBODY\r\nEND:BENV\r\nEND:BMSG\r\n'
state=Path.home()/'.local/state/asterisk-sms-bridge'
fd,filename=tempfile.mkstemp(prefix='outgoing-test-',suffix='.bmsg',dir=state)
with os.fdopen(fd,'wb') as f:f.write(data)
loop=GLib.MainLoop();result={'recipient_suffix':args.recipient[-4:],'push_calls':0,'automatic_retry':False,'originator_card':args.originator_card};transfer=None
start=time.monotonic()
def changed(iface,props,invalid,path):
 if str(path)==str(transfer) and iface==service+'.Transfer1' and props.get('Status') in ('complete','error'):
  result['transfer_status']=str(props['Status']);loop.quit()
match=bus.add_signal_receiver(changed,signal_name='PropertiesChanged',dbus_interface='org.freedesktop.DBus.Properties',bus_name=service,path_keyword='path')
try:
 ma=dbus.Interface(bus.get_object(service,sessions[0]),service+'.MessageAccess1')
 result['push_calls']=1
 transfer,props=ma.PushMessage(filename,'outbox',{'Transparent':dbus.Boolean(False),'Retry':dbus.Boolean(False),'Charset':'utf8'},timeout=25)
 if props.get('Status') in ('complete','error'):result['transfer_status']=str(props['Status'])
 else:
  timer=GLib.timeout_add_seconds(45,lambda:(loop.quit(),False)[1]);loop.run()
  if 'transfer_status' in result:GLib.source_remove(timer)
  else:result['transfer_status']='timeout-unknown; do not resend automatically'
except dbus.DBusException as exc:
 result['dbus_error']=exc.get_dbus_name()
 result['transfer_status']='method-error'
finally:
 result['seconds']=round(time.monotonic()-start,3)
 match.remove();Path(filename).unlink(missing_ok=True)
 print(json.dumps(result))
