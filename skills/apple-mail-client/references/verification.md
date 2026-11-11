# Verified contracts and limits

Checked 2026-11-02 on macOS 27.0.1, Apple Mail 16.0, library V10.
The local dictionary is the primary source for Mail's AppleScript classes and
commands, not a third-party MCP implementation or an App Intents API for other
apps.

## Primary web sources

- [Apple: Automate tasks in Mail](https://support.apple.com/guide/mail/automate-mail-tasks-mlhlp1120/mac): Mail supports AppleScript automation.
- [Apple: Search for emails](https://support.apple.com/guide/mail/search-for-emails-mlhlp1003/mac): mailbox scope, field/date filters and Boolean operators.
- [Apple: Send email messages](https://support.apple.com/en-ie/guide/mail/mlhlp1098/mac): saving drafts versus sending; UI scheduling and Undo Send.
- [Apple: Privacy & Security settings](https://support.apple.com/en-au/guide/mac-help/mchl211c911f/mac): Full Disk Access and Automation are separate permissions.
- [SQLite: URI filenames](https://www.sqlite.org/uri.html): `mode=ro`; `immutable=1` skips change detection and is unsuitable for this live database.
- [SQLite: Write-ahead logging](https://www.sqlite.org/wal.html): readers must account for the WAL; copying only the main database is not a live snapshot.
- [Python: email.parser](https://docs.python.org/3/library/email.parser.html): MIME parsing with `BytesParser` and explicit policy.

## Local contract

`/System/Applications/Mail.app/Contents/Resources/Mail.sdef` defines:

- Account `id`, `email addresses`, `enabled`, `account directory`; mailbox
  `name`, `account`, `container`; message `id`, `message id`, `source`, `content`.
- `reply`/`forward` return an outgoing message; `reply to all` defaults to false.
- Outgoing message `sender`, `subject`, `content`, recipients, `id`, and `save`;
  `send` returns a boolean. There is no supported arbitrary-header setter;
  hidden `html content` is explicitly a no-op.
- Message read/flag state and `move`; incoming attachment metadata and `save`.

The helper's index joins and EMLX layout are local observations, not public API.
Recheck them after Mail upgrades. Future test runs must use synthetic fixtures
for parser/search edge cases and a uniquely marked temporary draft for writes.
Do not send mail or alter existing messages merely to validate this skill.

## Observed verification

- Live discovery returned seven enabled accounts. Their private inventory is
  stored outside the repository, not hardcoded as a default sending identity.
- Live sender/name and account-scoped index queries worked. A cached EMLX read
  matched the native RFC Message-ID and left the unread flag unchanged.
- Nine synthetic tests cover read-only enforcement, Unicode/literal search,
  filter combinations, dates, deleted flags, MIME/EMLX boundaries, attachments,
  missing/partial/ambiguous files, incomplete summaries, and charset fallback.
- Two uniquely marked drafts were created without sending. UTF-8 body and
  recipients read back correctly; a saved draft remained readable after closing
  its outgoing object. One outgoing ID was 0, motivating content-based matching.
- An independent read-only forward-check covered scoped search, unsent replies,
  and reconciliation after a send timeout. All six AppleScript examples compiled
  against the installed Mail dictionary; both skill entrypoints validated.

No real send, live reply/forward, attachment round trip, requested archive/flag
workflow, or permission-denied path was exercised. Those procedures are
dictionary/source checked, not claimed end-to-end tested. Mail server delivery
is deliberately outside these smoke tests.

## Observed Mail deletion defect

Cleanup moved the scratch drafts into iCloud's Deleted Messages folder. Setting
`deleted status` to true on one of those trashed messages caused Mail to abort.
The diagnostic `Mail-2026-11-02-013625.ips` identifies `setIsDeleted:` and the
native persistence/transfer path. The writing reference therefore avoids that
API on this host. Mail was reopened to restore its initial running state.
Three scratch copies, with the two unique `Apple Mail Skill Test` subjects,
remain recoverable in Trash; no unrelated mail or whole mailbox was deleted.
