import importlib.util
from pathlib import Path
import sqlite3,tempfile,unittest
spec=importlib.util.spec_from_file_location('outgoing',Path(__file__).resolve().parents[1]/'outgoing.py')
o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
D='home.example.net'
class TestOutgoing(unittest.TestCase):
 def test_address_normalization_and_refusal(self):
  for uri in ['pjsip:"Contact" <sip:sms-972501234567@'+D+':5061;user=phone;transport=tls>','pjsips:sms-972501234567@'+D,'pjsip:sms-972501234567@'+D,'pjsip:sms-0501234567@'+D,'pjsip:972501234567@'+D,'pjsip:%2B972501234567@'+D,'pjsip:+972501234567@'+D,'sip:0501234567@'+D,'<sip:972501234567@'+D+':5061;transport=tls>']:
   self.assertEqual(o.number_from_uri(uri,D),'+972501234567')
  for uri in ['sip:+15551234567@'+D,'sip:+972501234567@evil.test','sip:1003@'+D,'sip:0501;bad@'+D]:
   with self.assertRaises(ValueError):o.number_from_uri(uri,D)
 def test_bmessage_length_unicode_originator_and_stuffing(self):
  data=o.make_bmessage('+972501234567','שלום Привет\nEND:MSG\nlast')
  self.assertIn(b'TEL:\r\nEND:VCARD\r\nBEGIN:BENV',data)
  head,body=data.split(b'BEGIN:MSG\r\n',1)
  size=int(head.split(b'LENGTH:')[1].split(b'\r\n')[0])
  self.assertEqual(size,len(b'BEGIN:MSG\r\n'+body.split(b'END:BBODY')[0]))
  self.assertIn(b'\r\n END:MSG\r\n',data)
 def test_crash_never_automatically_resends_and_request_is_idempotent(self):
  with tempfile.TemporaryDirectory() as temp:
   path=Path(temp)/'db';db=sqlite3.connect(path);box=o.Outbox(db)
   self.assertEqual(box.submit('a'*64,'+972501234567','test'),('queued',True))
   self.assertEqual(box.submit('a'*64,'+972501234567','test'),('queued',False))
   box.mark('a'*64,'submitting');db.close()
   db=sqlite3.connect(path);box=o.Outbox(db)
   self.assertEqual(box.recover(),['a'*64]);self.assertIsNone(box.next())
   self.assertEqual(box.submit('a'*64,'+972501234567','test'),('unknown',False))
   self.assertEqual(box.submit('b'*64,'+972501234567','next'),('queued',True))
   box.mark('b'*64,'handed-to-phone')
   self.assertIsNone(db.execute('select body from outgoing where id=?',('b'*64,)).fetchone()[0]);db.close()
 def test_expired_queued_message_is_never_sent(self):
  db=sqlite3.connect(':memory:');box=o.Outbox(db)
  box.submit('a'*64,'+972501234567','old')
  with db:db.execute('UPDATE outgoing SET created=created-90000')
  self.assertEqual(box.expire(),[('a'*64,'+972501234567')])
  self.assertIsNone(box.next())
  self.assertEqual(db.execute('SELECT status FROM outgoing').fetchone()[0],'expired')
  db.close()
 def test_limits_and_blank_text(self):
  db=sqlite3.connect(':memory:');box=o.Outbox(db)
  for body in ['','  ','a\x00b','я'*501]:
   with self.assertRaises(ValueError):box.submit('a'*64,'+972501234567',body)
  db.close()
if __name__=='__main__':unittest.main()
