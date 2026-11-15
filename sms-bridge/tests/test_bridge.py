import importlib.util
from pathlib import Path
import tempfile
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('bridge', Path(__file__).resolve().parents[1] / 'bridge.py')
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)


def bmsg(body, sender='+972501234567'):
    return ('BEGIN:BMSG\r\nVERSION:1.0\r\nSTATUS:UNREAD\r\nTYPE:SMS_GSM\r\n'
            'FOLDER:telecom/msg/inbox\r\nBEGIN:VCARD\r\nVERSION:2.1\r\n'
            f'TEL:{sender}\r\nEND:VCARD\r\nBEGIN:BENV\r\nBEGIN:BBODY\r\n'
            f'CHARSET:UTF-8\r\nLENGTH:99\r\nBEGIN:MSG\r\n{body}\r\nEND:MSG\r\n'
            'END:BBODY\r\nEND:BENV\r\nEND:BMSG\r\n').encode()


class TestParsing(unittest.TestCase):
    def test_unicode_multiline_and_literal_marker(self):
        sender, body = b.parse_bmessage(bmsg('Привет! שלום!\r\nEND:MSG\r\nlast'))
        self.assertEqual(sender, '+972501234567')
        self.assertEqual(body, 'Привет! שלום!\nEND:MSG\nlast')

    def test_incomplete_or_wrong_encoding_is_not_sent(self):
        for raw in (bmsg('hello')[:-12], bmsg('hello').replace(b'hello', b'\xff'),
                    bmsg('hello').replace(b'TYPE:SMS_GSM', b'TYPE:MMS'), bmsg('a\x00b')):
            with self.assertRaises((ValueError, UnicodeError)):
                b.parse_bmessage(raw)

    def test_handle_reuse_differs_but_session_reconnect_does_not(self):
        p = dict(Timestamp='20261114T201500', SenderAddress='123', Type='sms-gsm', Size=20)
        original = b.fingerprint('device', '/session1/message42', p)
        self.assertEqual(original, b.fingerprint('device', '/session2/message42', p))
        p['Timestamp'] = '20261114T201600'
        self.assertNotEqual(original, b.fingerprint('device', '/session2/message42', p))


class TestQueue(unittest.TestCase):
    def test_durable_reopen_dedup_retry_and_accept(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'queue.sqlite3'
            store = b.Store(path)
            cutoff = store.value('cutoff')
            store.enqueue('key', 'sender', '20261114T202654', 'Привет! שלום!')
            store.enqueue('key', 'sender', '20261114T202654', 'Привет! שלום!')
            row = store.next_message()
            call = row['call_id']
            store.db.close()
            store = b.Store(path)
            self.assertEqual(store.value('cutoff'), cutoff)
            self.assertEqual(store.next_message()['body'], 'Привет! שלום!')
            store.result('key', 503, 1)
            self.assertGreater(store.next_message()['due'], time.time())
            self.assertEqual(store.next_message()['call_id'], call)
            store.result('key', 202, 2)
            self.assertIsNone(store.next_message())
            self.assertTrue(store.seen('key'))
            row = store.db.execute('SELECT * FROM messages').fetchone()
            self.assertEqual(row['status'], 'accepted')
            self.assertIsNone(row['body'])
            self.assertIsNone(row['sender'])
            store.db.close()

    def test_permanent_rejection_preserves_message_and_next_can_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = b.Store(Path(tmp) / 'db')
            store.enqueue('a', 'sender', '20261114T202654', 'do not lose')
            store.result('a', 403, 1)
            self.assertIsNone(store.next_message())
            self.assertEqual(store.db.execute('SELECT body FROM messages').fetchone()[0], 'do not lose')
            store.enqueue('b', 'sender', '20261114T202654', 'next')
            self.assertEqual(store.next_message()['id'], 'b')
            with patch.object(b, 'MAX_QUEUE', 2):
                with self.assertRaises(RuntimeError):
                    store.enqueue('c', 'sender', '20261114T202654', 'full')
            store.db.close()

    def test_iphone_timestamp_shift_and_handle_change_after_accept_and_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'db'
            store = b.Store(path)
            self.assertTrue(store.enqueue('notification-handle', 'FUND', '20261114T202654', 'code 123456'))
            store.result('notification-handle', 200, 1)
            store.db.close()
            store = b.Store(path)
            self.assertFalse(store.enqueue('listing-handle', 'FUND', '20261114T202653', 'code 123456'))
            self.assertTrue(store.seen('listing-handle'))
            self.assertIsNone(store.next_message())
            self.assertEqual(store.db.execute('SELECT count(*) FROM messages').fetchone()[0], 1)
            # Distinct body, sender, or sufficiently later genuine repetition survives.
            self.assertTrue(store.enqueue('new-code', 'FUND', '20261114T202654', 'code 654321'))
            self.assertTrue(store.enqueue('other-sender', 'OTHER', '20261114T202654', 'code 123456'))
            self.assertTrue(store.enqueue('later', 'FUND', '20261114T202657', 'code 123456'))
            store.db.close()

    def test_duplicate_while_original_pending_does_not_create_second_job(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = b.Store(Path(tmp) / 'db')
            store.enqueue('first', 'sender', '20261114T202654', 'same')
            self.assertFalse(store.enqueue('second', 'sender', '20261114T202653', 'same'))
            self.assertEqual(store.db.execute('SELECT count(*) FROM messages').fetchone()[0], 1)
            store.db.close()


class FakeSocket:
    def __init__(self, chunks): self.chunks = iter(chunks)
    def settimeout(self, timeout): pass
    def recv(self, size): return next(self.chunks, b'')


class TestSip(unittest.TestCase):
    def test_fragmented_provisional_and_accepted_response(self):
        msg = (b'SIP/2.0 100 Trying\r\nCall-ID: abc\r\nCSeq: 1 MESSAGE\r\nContent-Length: 0\r\n\r\n'
               b'SIP/2.0 202 Accepted\r\nCall-ID: abc\r\nCSeq: 1 MESSAGE\r\nContent-Length: 3\r\n\r\nxyz')
        self.assertEqual(b.read_final(FakeSocket([msg[:40], msg[40:-1], msg[-1:]]), 'abc'), 202)

    def test_unrelated_or_missing_final_is_not_success(self):
        with self.assertRaises(ValueError):
            b.read_final(FakeSocket([b'SIP/2.0 202 Accepted\r\nCall-ID: wrong\r\nCSeq: 1 MESSAGE\r\n\r\n']), 'abc')
        with self.assertRaises(ConnectionError):
            b.read_final(FakeSocket([]), 'abc')

    def test_utf8_length_and_header_injection(self):
        config = dict(sip_target='sip:user@sip.linphone.org', from_domain='test.example')
        row = dict(sender='evil\r\nInjected: yes"', stamp='date', body='שלום Привет', call_id='abcdef1234567890')
        request, call = b.sip_request(config, row, ('192.168.50.10', 1234))
        header, body = request.split(b'\r\n\r\n', 1)
        self.assertNotIn(b'\r\nInjected:', header)
        self.assertIn(f'Content-Length: {len(body)}'.encode(), header)
        self.assertIn('שלום Привет'.encode(), body)
        self.assertNotIn(b'Authorization:', header)


if __name__ == '__main__':
    unittest.main()
