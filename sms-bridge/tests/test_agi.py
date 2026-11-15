import importlib.util,importlib.machinery,io,unittest
from pathlib import Path
path=Path(__file__).resolve().parents[1]/'sms-submit.agi'
loader=importlib.machinery.SourceFileLoader('submit_agi',str(path));spec=importlib.util.spec_from_loader(loader.name,loader);m=importlib.util.module_from_spec(spec);loader.exec_module(m)
class TestAgi(unittest.TestCase):
 def read_field(self,text):
  data=text.encode();m.IN=io.BytesIO(b'200 result=1 ('+str(len(data)).encode()+b')\n200 result=1 ('+data+b')\n');m.OUT=io.BytesIO()
  self.assertEqual(m.field('${MESSAGE(body)}'),text);self.assertEqual(m.IN.read(),b'')
 def test_preserves_uri_lengths_and_last_bytes(self):
  for n in range(1,80):self.read_field('x'*n+'.org')
  self.read_field('pjsip:sms-972501234567@home.example.net')
 def test_multiline_parentheses_unicode_and_zero(self):
  for text in ['', 'Привет! שלום!\n)\n200 result=1 (not a command)\nlast', '  keep spaces  ']:self.read_field(text)
 def test_mismatched_length_rejected(self):
  m.IN=io.BytesIO(b'200 result=1 (1)\n200 result=1 (longer)\n');m.OUT=io.BytesIO()
  with self.assertRaises(ValueError):m.field('${MESSAGE(body)}')
if __name__=='__main__':unittest.main()
