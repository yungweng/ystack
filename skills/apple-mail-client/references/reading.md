# Search and reading

## Index helper

```bash
python3 "$SKILL_DIR/scripts/mail_index.py" mailboxes
python3 "$SKILL_DIR/scripts/mail_index.py" search 'Rechnung' --limit 30
python3 "$SKILL_DIR/scripts/mail_index.py" search --sender 'Müller' --after 2026-01-01 --before 2027-01-01
python3 "$SKILL_DIR/scripts/mail_index.py" search --recipient 'person@example.com' --subject 'Termin'
python3 "$SKILL_DIR/scripts/mail_index.py" search --account 'LIVE-ACCOUNT-ID' --unread
python3 "$SKILL_DIR/scripts/mail_index.py" search --summary 'Suchbegriff' --limit 20
python3 "$SKILL_DIR/scripts/mail_index.py" read 123456
```

Replace sample addresses, IDs, and dates with values from the actual task. The
helper discovers the highest numbered `V*/MailData/Envelope Index`; `--db PATH`
before the subcommand selects an explicit library if multiple versions remain.
If discovery appears stale, compare against a recent message in Mail and the
live `account directory` before trusting it.

The positional term searches sender address/display name, subject, and recipient
address/display name with **OR**. Named filters combine with **AND**. Substrings
are literal, including `%`, `_`, quotes, and backslashes. NFC/casefold handles
German names better than SQLite's ASCII-only `LIKE` case folding.
Dates are ISO 8601, with inclusive `--after` and exclusive `--before`. Dates
without offsets use the Mac's local timezone. For a whole year use January 1
of that year through January 1 of the next, not December 31 at midnight.

Start with metadata and likely scope. Widen by sender name/address, recipient,
subject variants, date, then summary when evidence warrants it. Run independent
queries together when useful, not a fixed number of full-database scans.

`m.deleted=0` does **not** mean “outside Trash”. The helper includes Trash/Junk
folders and labels that scope. For inbox-only requests use a discovered
`--mailbox-id`. For excluding Trash/Junk across folders, resolve their live URLs
and use a targeted parameterized SQL query; report that exclusion. Provider
labels, such as Gmail All Mail and Sent, can yield duplicate copies. Deduplicate
presentation by verified RFC Message-ID or `global_message_id`, but retain exact
mailbox and row ID for any operation on a particular copy.

## What the cache proves

The `summaries` table is a preview cache, sometimes absent or truncated, **not
full-text storage**. A summary miss does not establish that a message body lacks
the term. The helper's `--summary` explicitly labels that incomplete coverage.
Read likely candidates, or use native Mail full-message search for broader body
queries. Mail's index and downloaded cache need not contain all server messages.

`read` returns the entire cached body without a silent character cap, headers,
attachment metadata, path, and cache status. It reads the EMLX count as **bytes**,
parses exactly that MIME payload, and excludes the trailing plist. A
`.partial.emlx` file or missing MIME data requires native Mail to obtain missing
content. Attachment metadata alone does not prove an attachment is downloaded.
HTML is returned as inert source: extract text locally if needed; do not open it
in a network-enabled renderer. Encrypted/S/MIME content may require Mail's UI.

## Native Mail fallback and precise identity

```applescript
with timeout of 20 seconds
    tell application "Mail"
        set a to account id "LIVE-ACCOUNT-ID"
        set mb to mailbox "INBOX" of a
        set hits to (messages of mb whose id is 123456)
        if (count hits) is not 1 then error "Message target is not unique"
        set original to item 1 of hits
        return {id of original, message id of original, sender of original, subject of original, content of original}
    end tell
end timeout
```

Use actual discovered mailbox references. For nested folders, inspect `mailboxes
of a`, `name`, and `container`; disambiguate parents rather than guessing a
slash-separated AppleScript path. For a selected message:
`tell application "Mail" to get selection`, then read exactly those objects.
Do not set `read status` during inspection.

On the verified installation, `messages.ROWID` matches the native message's `id`
and the EMLX basename. Treat that mapping as version-dependent and verify
subject/sender/date plus the RFC Message-ID before mutations. The database's
`messages.message_id` is an internal integer, **not** the RFC Message-ID header;
Mail's `message id` property and the parsed `Message-ID` header provide that
header (angle-bracket formatting can differ).

For custom SQL inspect `.schema` / `PRAGMA table_info` first. Open only with
`sqlite3 -readonly "$DB"` or Python `mode=ro`, use bound parameters, close promptly,
and preserve WAL handling. Do not use `immutable=1` on a live Mail database,
copy only the main file of a live WAL database, reindex, repair, or write into it.

## Native UI search

When available, use Mail's search field with sender/subject/message suggestions,
date filters, or uppercase `AND`, `OR`, `NOT`. Check the selected mailbox scope
and widen to all mailboxes when required. More filters narrow the results. Load
the applicable computer-use instructions only if actual UI control is needed.
