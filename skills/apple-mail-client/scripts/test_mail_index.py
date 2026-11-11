import argparse
import importlib.util
import sqlite3
import tempfile
import unittest
from contextlib import closing
from email.message import EmailMessage
from pathlib import Path

spec = importlib.util.spec_from_file_location('mail_index', Path(__file__).with_name('mail_index.py'))
mail = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mail)


class MailIndexTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.library = Path(self.temp.name) / 'V10'
        self.database = self.library / 'MailData/Envelope Index'
        self.database.parent.mkdir(parents=True)
        with closing(sqlite3.connect(self.database)) as db:
            db.executescript('''
                CREATE TABLE messages (message_id,global_message_id,date_received,read,flagged,deleted,sender,subject,mailbox,summary);
                CREATE TABLE addresses (address,comment);
                CREATE TABLE subjects (subject);
                CREATE TABLE mailboxes (url,total_count,unread_count);
                CREATE TABLE summaries (summary);
                CREATE TABLE recipients (message,address);
                INSERT INTO addresses VALUES ('sender@example.com','Müller'),('to@example.com','Empfänger');
                INSERT INTO subjects VALUES ('Literal %_ and quote '' test');
                INSERT INTO mailboxes VALUES ('imap://account/INBOX',3,1);
                INSERT INTO summaries VALUES ('preview only');
                INSERT INTO messages VALUES (-123,22,1735689600,0,0,0,1,1,1,1);
                INSERT INTO messages VALUES (-124,23,1735776000,1,0,0,1,1,1,1);
                INSERT INTO messages VALUES (-125,24,1735689600,0,0,1,1,1,1,1);
                INSERT INTO recipients VALUES (1,2),(1,2);
            ''')
            db.commit()
        self.db = mail.connect(self.database)
        self.addCleanup(self.db.close)

    def search(self, **kwargs):
        defaults = dict(mailbox_id=None,account=None,unread=False,after=None,before=None,
                        sender=None,subject=None,recipient=None,summary=None,term=None,limit=30)
        defaults.update(kwargs)
        return mail.search(self.db, argparse.Namespace(**defaults))

    def make_emlx(self, partial=False):
        msg = EmailMessage()
        msg['From'] = 'sender@example.com'
        msg['To'] = 'to@example.com'
        msg['Message-ID'] = '<fixture@example.com>'
        msg.set_content('Grüße aus Münster. Volltext nach dem Preview.\n')
        msg.add_attachment(b'example', maintype='application', subtype='octet-stream', filename='prüfen.bin')
        raw = msg.as_bytes()
        path = self.library / 'account/INBOX.mbox/Data/Messages' / ('1.partial.emlx' if partial else '1.emlx')
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(str(len(raw)).encode() + b'\n' + raw + b'<?xml version="1.0"?><plist>NOT BODY</plist>')
        return path

    def test_connection_rejects_writes(self):
        with self.assertRaises(sqlite3.OperationalError):
            self.db.execute('DELETE FROM messages')
        self.assertEqual(self.db.execute('SELECT count(*) FROM messages').fetchone()[0],3)

    def test_literal_substrings_and_unicode_normalization(self):
        self.assertEqual(len(self.search(sender='MÜLLER')['messages']),2)
        self.assertEqual(len(self.search(subject="%_ and quote '")['messages']),2)
        self.assertEqual(self.search(term="' OR 1=1 --")['messages'],[])

    def test_metadata_or_named_filters_and_recipient_no_duplicates(self):
        self.assertEqual([r['row_id'] for r in self.search(term='EMPFÄNGER')['messages']],[1])
        self.assertEqual(self.search(sender='Müller',subject='missing')['messages'],[])
        self.assertEqual(self.search(account='wrong')['messages'],[])
        self.assertEqual(len(self.search(account='account')['messages']),2)

    def test_half_open_dates_unread_and_deleted(self):
        result=self.search(after='2025-01-01T00:00:00+00:00',before='2025-01-02T00:00:00+00:00',unread=True)
        self.assertEqual([r['row_id'] for r in result['messages']],[1])
        self.assertIn('+',result['messages'][0]['received_local'])

    def test_emlx_bytes_mime_and_plist_boundary(self):
        self.make_emlx()
        result=mail.read_message(self.db,self.database,1)
        self.assertIn('Grüße aus Münster',result['body'])
        self.assertNotIn('NOT BODY',result['body'])
        self.assertEqual(result['attachments'][0]['filename'],'prüfen.bin')
        self.assertEqual(result['headers']['Message-ID'],['<fixture@example.com>'])
        self.assertEqual(result['index_message_id'],-123)

    def test_missing_partial_and_ambiguous_cache(self):
        self.assertIsNone(mail.read_message(self.db,self.database,1)['body'])
        self.make_emlx(partial=True)
        self.assertEqual(mail.read_message(self.db,self.database,1)['cache_status'],'partial')
        self.make_emlx()
        with self.assertRaisesRegex(ValueError,'Multiple EMLX'):
            mail.read_message(self.db,self.database,1)

    def test_truncated_payload_and_missing_database_fail_closed(self):
        path=self.make_emlx()
        path.write_bytes(b'999999\nshort')
        with self.assertRaisesRegex(ValueError,'Truncated'):
            mail.parse_emlx(path)
        absent=Path(self.temp.name)/'nonexistent'
        with self.assertRaises(sqlite3.OperationalError):
            mail.connect(absent)
        self.assertFalse(absent.exists())

    def test_summary_search_does_not_claim_full_text(self):
        result=self.search(summary='Preview')
        self.assertEqual(len(result['messages']),2)
        self.assertIn('incomplete',result['body_coverage'])
        self.assertEqual(self.search(summary='Volltext')['messages'],[])

    def test_unknown_charset_has_explicit_fallback(self):
        path=self.make_emlx()
        raw=b'Content-Type: text/plain; charset="x-unknown-legacy"\n\nLegacy body\n'
        path.write_bytes(str(len(raw)).encode()+b'\n'+raw+b'<plist/>')
        result=mail.parse_emlx(path)
        self.assertEqual(result['body'],'Legacy body\n')
        self.assertIn('fallback',result['body_warning'])


if __name__ == '__main__':
    unittest.main()
