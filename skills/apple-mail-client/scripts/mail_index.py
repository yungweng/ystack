#!/usr/bin/env python3
"""Bounded, read-only Apple Mail index search and cached EMLX reading."""

import argparse
import json
import sqlite3
import sys
import time
import unicodedata
from contextlib import closing
from datetime import datetime
from email import policy
from email.parser import BytesParser
from pathlib import Path
from urllib.parse import urlsplit


def discover_database():
    root = Path.home() / 'Library/Mail'
    candidates = [p for p in root.glob('V*/MailData/Envelope Index')
                  if p.parent.parent.name[1:].isdigit()]
    if not candidates:
        raise ValueError('No readable Envelope Index found; check Full Disk Access or use Mail scripting')
    return max(candidates, key=lambda p: int(p.parent.parent.name[1:]))


def fold(value):
    return unicodedata.normalize('NFC', value or '').casefold()


def connect(database):
    db = sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True, timeout=2)
    db.row_factory = sqlite3.Row
    db.execute('PRAGMA query_only=ON')
    db.create_function('contains_text', 2, lambda value, term: int(fold(term) in fold(value)))
    deadline = time.monotonic() + 15
    db.set_progress_handler(lambda: int(time.monotonic() > deadline), 10000)
    return db


BASE = '''SELECT m.ROWID AS row_id, m.message_id AS index_message_id,
                 m.global_message_id, m.date_received, m.read, m.flagged, m.deleted,
                 a.address AS sender, a.comment AS sender_name, s.subject,
                 b.ROWID AS mailbox_id, b.url AS mailbox_url
          FROM messages m
          LEFT JOIN addresses a ON a.ROWID=m.sender
          LEFT JOIN subjects s ON s.ROWID=m.subject
          JOIN mailboxes b ON b.ROWID=m.mailbox'''


def metadata(row):
    result = dict(row)
    stamp = result.get('date_received')
    if stamp is not None:
        result['received_local'] = datetime.fromtimestamp(stamp).astimezone().isoformat()
    result['account_id'] = urlsplit(result['mailbox_url']).netloc
    return result


def search(db, args):
    clauses, params = ['m.deleted=0'], []
    for column, value in [('b.ROWID', args.mailbox_id)]:
        if value is not None:
            clauses.append(column + '=?')
            params.append(value)
    if args.account:
        clauses.append('b.url LIKE ? ESCAPE \'\\\'')
        escaped = args.account.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
        params.append('imap://' + escaped + '/%')
    if args.unread:
        clauses.append('m.read=0')
    for operator, value in [('>=', args.after), ('<', args.before)]:
        if value:
            # Naive ISO timestamps/dates use the machine's local timezone.
            stamp = datetime.fromisoformat(value).timestamp()
            clauses.append('m.date_received' + operator + '?')
            params.append(stamp)
    fields = {
        'sender': '(contains_text(a.address,?) OR contains_text(a.comment,?))',
        'subject': 'contains_text(s.subject,?)',
        'recipient': '''EXISTS (SELECT 1 FROM recipients r JOIN addresses ra ON ra.ROWID=r.address
                                WHERE r.message=m.ROWID AND
                                (contains_text(ra.address,?) OR contains_text(ra.comment,?)))''',
        'summary': '''EXISTS (SELECT 1 FROM summaries su WHERE su.ROWID=m.summary
                              AND contains_text(su.summary,?))''',
    }
    for field, expression in fields.items():
        value = getattr(args, field)
        if value:
            clauses.append(expression)
            params.extend([value] * expression.count('?'))
    if args.term:
        expressions = [fields[x] for x in ('sender', 'subject', 'recipient')]
        clauses.append('(' + ' OR '.join(expressions) + ')')
        params.extend([args.term] * sum(x.count('?') for x in expressions))
    params.append(args.limit)
    rows = db.execute(BASE + ' WHERE ' + ' AND '.join(clauses) +
                      ' ORDER BY m.date_received DESC, m.ROWID DESC LIMIT ?', params)
    return {'scope': 'local index; excludes deleted flag, includes Trash/Junk folders',
            'body_coverage': 'summaries only, incomplete' if args.summary else 'not searched',
            'limit': args.limit, 'messages': [metadata(row) for row in rows]}


def parse_emlx(path):
    with path.open('rb') as stream:
        length_line = stream.readline(64)
        if not length_line.endswith(b'\n') or not length_line.strip().isdigit():
            raise ValueError('Invalid EMLX byte-count header')
        size = int(length_line)
        if size > 128 * 1024 * 1024:
            raise ValueError('EMLX exceeds 128 MiB; use a targeted native Mail read')
        raw = stream.read(size)
        if len(raw) != size:
            raise ValueError('Truncated EMLX payload')
    message = BytesParser(policy=policy.default).parsebytes(raw)
    body = message.get_body(preferencelist=('plain', 'html'))
    body_warning = None
    body_text = None
    if body is not None:
        try:
            body_text = body.get_content()
        except (LookupError, UnicodeError):
            body_text = (body.get_payload(decode=True) or b'').decode('utf-8', errors='replace')
            body_warning = 'Declared charset could not be decoded; UTF-8 replacement fallback, verify in Mail'
    attachments = [
        {'filename': part.get_filename(), 'mime_type': part.get_content_type(),
         'disposition': part.get_content_disposition()}
        for part in message.walk() if part.get_filename() or part.is_attachment()
    ]
    return {'emlx_path': str(path),
            'cache_status': 'partial' if path.name.endswith('.partial.emlx') else 'local cache; server completeness unverified',
            'headers': {name: message.get_all(name, []) for name in
                        ('From', 'To', 'Cc', 'Bcc', 'Subject', 'Date', 'Message-ID', 'Reply-To', 'References', 'In-Reply-To')},
            'body_type': body.get_content_type() if body else None,
            'body': body_text,
            'body_warning': body_warning,
            'attachments': attachments,
            'mime_defects': [str(defect) for part in message.walk() for defect in part.defects]}


def read_message(db, database, row_id):
    row = db.execute(BASE + ' WHERE m.ROWID=?', (row_id,)).fetchone()
    if row is None:
        raise ValueError('No message with that local row ID')
    result = metadata(row)
    library = database.parent.parent
    account = result['account_id']
    # Never turn an unverified mailbox URL into an arbitrary filesystem path.
    root = library / account if account and account not in ('.', '..') and Path(account).name == account else library
    if not root.is_dir():
        root = library
    matches = []
    for p in root.rglob(str(row_id) + '.*emlx'):
        if p.name in (str(row_id) + '.emlx', str(row_id) + '.partial.emlx'):
            matches.append(p)
            if len(matches) > 1:
                raise ValueError('Multiple EMLX candidates; resolve through Mail before reading')
    if not matches:
        result.update({'body': None, 'cache_status': 'EMLX not found; use native Mail for content'})
    else:
        result.update(parse_emlx(matches[0]))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', type=Path, help='Explicit Envelope Index path')
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('mailboxes')
    find = commands.add_parser('search')
    find.add_argument('term', nargs='?', help='Literal substring across sender, subject, recipients (OR)')
    for field in ('sender', 'subject', 'recipient', 'summary', 'account', 'after', 'before'):
        find.add_argument('--' + field)
    find.add_argument('--mailbox-id', type=int)
    find.add_argument('--unread', action='store_true')
    find.add_argument('--limit', type=int, default=30)
    read = commands.add_parser('read')
    read.add_argument('row_id', type=int)
    args = parser.parse_args()
    if args.command == 'search' and not 1 <= args.limit <= 200:
        parser.error('--limit must be between 1 and 200')
    try:
        database = args.db.expanduser() if args.db else discover_database()
        with closing(connect(database)) as db:
            if args.command == 'search':
                result = search(db, args)
            elif args.command == 'read':
                result = read_message(db, database, args.row_id)
            else:
                result = [dict(row) for row in db.execute(
                    'SELECT ROWID AS mailbox_id,url,total_count,unread_count FROM mailboxes ORDER BY url')]
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, sqlite3.Error) as exc:
        print('Mail read failed: ' + str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
