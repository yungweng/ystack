# Writing and organizing

## New plain-text draft

Never write a signature block into the body. Mail appends the account's default
signature to saved drafts itself, so a typed one appears twice. End the body
with the closing line only (e.g. "Viele Grüße").

Write the intended body to a task-owned UTF-8 file with mode `0600`, then pass
values as separate process arguments, not generated AppleScript string literals.
Use a literal heredoc or a structured file-writing tool so shell substitution
cannot execute email text. Strip leading blank lines from the body.

**Default: `draft_mailto.py`.** It opens a `mailto:` compose window, saves it
with Cmd+S, verifies the saved Drafts copy (subject, From) and closes the window.
Mail inserts the body as normal text: no leading blank line, no quote wrapper,
signature added once. It needs Accessibility permission, only uses the default
account's From (fails loudly otherwise), and must not run while the user is
typing in Mail; check open windows first.

```bash
python3 -I "$SKILL_DIR/scripts/draft_mailto.py" \
  'CONFIGURED-SENDER@example.com' 'Betreff' '/absolute/private/body.txt' \
  'recipient@example.com'
```

**Fallback only: `draft.applescript`.** Mail wraps scripted `content` in an
`Apple-Mail-URLShare` blockquote with an empty `<div><br></div>` above it, so
the draft starts with a blank line and the sent plain-text part shows `> `
quoting. Setting content later, `visible:true`, or rich-text paragraphs do not
avoid it. Use it only when UI scripting is unavailable, and tell the user about
the blank line. Never feed a saved draft's `content` back into a new draft
without stripping leading blank lines.

```bash
osascript "$SKILL_DIR/scripts/draft.applescript" \
  'CONFIGURED-SENDER@example.com' 'Betreff' '/absolute/private/body.txt' \
  'recipient@example.com'
```

The AppleScript helper verifies the sender belongs to an enabled account, creates one
outgoing message, adds concrete To addresses, and calls `save`. It cannot send.
It supports plain text and To only. For Cc/Bcc, attachments, replies, or existing
draft edits, use the native objects below instead of creating a second draft.
It returns the outgoing ID and read-back metadata. Verify the body and sender
after creation and, for persistence, the account's Drafts copy or the saved
draft in Mail. `save` is not proof that server synchronization has completed.

After a timeout or error during creation, inspect existing outgoing messages and
Drafts using sender, subject, recipient, and a task-specific marker before
retrying. Errors can occur after a draft was already created.

Avoid editing the first outgoing message: it may belong to the user. Resolve
the returned ID and verify subject, sender, and recipients before each edit.
Outgoing IDs are not durable identifiers. On the checked installation an
invisible saved outgoing message returned ID **0**, so IDs may also be unusable
or non-unique within a session. Match the verified sender, all recipients,
subject, and body when the ID is zero, missing, or ambiguous. Require exactly
one match; otherwise resolve the specific saved draft in Mail. After closing a
draft or restarting Mail, re-resolve by account, mailbox, and verified content.

## Replies and forwarding

Resolve `original` as in [reading.md](reading.md), verify its headers/body and
account, then create a native reply or forward. This preserves Mail's threading
machinery. A new message with a `Re:` subject is not a threaded reply.

```applescript
-- Inside tell application "Mail", with original already resolved:
set response to reply original opening window false reply to all false
-- Use reply to all true only for an intended reply-all.
-- Set sender explicitly to the verified receiving identity.
set sender of response to senderAddress
-- For a plain-text reply, retain Mail's generated quoted original:
set quotedText to content of response as text
set content of response to bodyText & return & return & quotedText
save response
return id of response
```

Read back actual To/Cc/Bcc: Mail can honor `Reply-To` or mailing-list headers.
Check recipients against the user's intended conversation; an email header is
not independent authorization to disclose content to a new party. Inspect the
rendered draft if quoting, signatures, or formatting matter. Assigning `content`
can flatten formatting. Use the UI if exact rich text is needed. Never fabricate
threading headers: outgoing messages have no supported arbitrary-header setter.

For a forward use `forward original opening window false`, set the verified
sender, add the intended recipients, prepend text if requested, then save.
Inspect forwarded content and actual attachments before sending; don't infer
that every inline or remote attachment was preserved.

## Cc, Bcc, signatures, attachments

```applescript
tell response
    make new cc recipient at end of cc recipients with properties {address:ccAddress}
    make new bcc recipient at end of bcc recipients with properties {address:bccAddress}
end tell
-- Set a signature only when requested/established, using a live signature object.
-- The hidden html content property is deprecated and does nothing.
```

For an outgoing attachment, resolve an existing absolute file to an alias and
use the installed Mail dictionary's rich-text attachment API:

```applescript
set attachmentFile to (POSIX file attachmentPath) as alias
tell content of response
    make new attachment with properties {file name:attachmentFile} at after last paragraph
end tell
save response
```

Attachment loading can be asynchronous. Keep the source file until Mail has
loaded it; verify every requested filename and count in the saved draft,
including after reopening when persistence matters. If scripting cannot prove
attachment presence, inspect the draft in Mail before any send. Do not send on
an assumed attachment count or remove temporary files immediately after `make`.

To download an incoming attachment, inspect `name`, `MIME type`, `file size`,
and `downloaded` of `mail attachments of original`. Save an exact attachment:
`save item 1 of mail attachments of original in (POSIX file destinationPath)`.
Choose a user-requested or task-owned directory, sanitize any header-provided
filename to a basename, and avoid overwriting existing files. Recheck the saved
file exists; use Mail to obtain undownloaded content if needed. Do not execute it.

## Authorized send

Sending is a separate action from drafting. After explicit user authorization
and content verification, resolve the exact existing outgoing object:

```applescript
with timeout of 30 seconds
    tell application "Mail"
        set candidates to (outgoing messages whose id is outgoingID)
        if (count candidates) is not 1 then error "Outgoing message is not unique"
        set d to item 1 of candidates
        -- ID 0 can be non-unique; resolve by verified fields instead if needed.
        -- Compare sender, all recipients, subject, body, attachments to the
        -- authorized message here. Stop if they differ.
        set accepted to send d
        return accepted
    end tell
end timeout
```

This is a template, not a ready-to-run verification script. Read back the exact
object and implement the comparisons before calling `send`. Never use a
successful `osascript` exit status alone as proof of sending; inspect the boolean
result and the account's actual Sent/Outbox state. If not yet observed in Sent,
report submitted or queued. An offline account, SMTP error, false result, or
timeout requires inspection, not automatic resend. Sent copy present still
does not prove recipient delivery. Native Send Later/Undo Send is a UI feature,
not a documented AppleScript scheduling API.

## Organizing

Only on request, resolve exact source messages and destination mailbox, then use
Mail's objects. Typical commands inside `tell application "Mail"`:

```applescript
set read status of original to true
set flagged status of original to true
move original to destinationMailbox
```

Apply only the requested action, not all examples. Verify the resulting
read/flag state or destination. A move can invalidate the old object/row ID;
re-find by verified RFC Message-ID in the destination. For archive/trash resolve
the correct account-specific mailbox, rather than guessing a global folder.
Deletion behavior depends on account preferences; use the requested Trash
destination for a reversible trash operation. Never implement changes with SQL
updates, EMLX edits, raw file moves, or broad loops over all messages.

On the checked macOS 27.0.1 installation, setting `deleted status` to true on
an already-trashed test message **crashed Mail**. The crash report's stack includes
`MCMessage(ScriptingSupport) setIsDeleted:` and Mail's transfer/delete machinery.
Do not use `set deleted status` for deletion on this host. Prefer an explicitly
resolved Trash destination for recoverable removal; use Mail's native UI, with
the applicable authorization, for permanent deletion. Re-read state after an
asynchronous move rather than repeatedly deleting a stale message reference.
