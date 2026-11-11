#!/usr/bin/env python3
"""Create ONE clean Apple Mail draft via a mailto: URL. It never sends.

Unlike draft.applescript, Mail inserts a mailto body as normal text: no
URLShare blockquote, no leading blank line, account signature added once.

Usage: draft_mailto.py SENDER SUBJECT BODY_FILE TO [TO ...]

SENDER must match the From that Mail picks (the default account); the script
fails if it differs instead of silently using another identity. The body must
end with the closing line only; Mail appends the signature itself.
Needs Accessibility permission for the shell host (System Events, Cmd+S/W).
"""
import email
import pathlib
import subprocess
import sys
import time
import urllib.parse
from email import policy

DRAFTS_GLOB = "V*/*/Drafts.mbox/**/Messages/*.emlx"


def osa(script, *args):
    r = subprocess.run(["osascript", "-e", script, *args], capture_output=True, text=True, timeout=60)
    if r.returncode:
        raise SystemExit(f"osascript failed: {r.stderr.strip()}")
    return r.stdout.strip()


def find_saved(subject, since):
    root = pathlib.Path.home() / "Library/Mail"
    for p in root.glob(DRAFTS_GLOB):
        if p.stat().st_mtime < since:
            continue
        raw = p.read_bytes()
        n = int(raw.split(b"\n", 1)[0])
        msg = email.message_from_bytes(raw.split(b"\n", 1)[1][:n], policy=policy.default)
        if msg["Subject"] == subject:
            return msg
    return None


def main():
    if len(sys.argv) < 5:
        raise SystemExit(__doc__)
    sender, subject, body_path, *to = sys.argv[1:]
    if any(c in subject for c in "\r\n") or not all("@" in t for t in to):
        raise SystemExit("Invalid subject or recipient")
    body = pathlib.Path(body_path).read_text(encoding="utf-8").strip("\n")
    if "\n--\n" in body or "\n-- \n" in body:
        raise SystemExit("Body contains a signature block; Mail adds the signature itself")
    open_windows = osa('tell application "System Events" to tell process "Mail" to get name of windows')
    if subject in [w.strip() for w in open_windows.split(",")]:
        raise SystemExit("A Mail window with this subject is already open")

    q = urllib.parse.quote
    url = f"mailto:{','.join(q(t, safe='@') for t in to)}?subject={q(subject)}&body={q(body)}"
    started = time.time() - 1
    subprocess.run(["open", url], check=True)

    raise_and_save = '''on run argv
set t to item 1 of argv
tell application "Mail" to activate
tell application "System Events" to tell process "Mail"
repeat 40 times
if exists window t then exit repeat
delay 0.25
end repeat
if not (exists window t) then error "compose window did not open"
perform action "AXRaise" of window t
delay 0.4
if name of front window is not t then error "compose window is not frontmost"
keystroke "s" using command down
end tell
end run'''
    osa(raise_and_save, subject)

    msg = None
    for _ in range(40):
        msg = find_saved(subject, started)
        if msg:
            break
        time.sleep(0.25)
    if not msg:
        raise SystemExit("Draft not found in Drafts after save; window left open for inspection")
    if sender.lower() not in str(msg["From"]).lower():
        raise SystemExit(f"Mail used From {msg['From']!r}, not {sender!r}; window left open, fix sender manually")

    close = '''on run argv
set t to item 1 of argv
tell application "System Events" to tell process "Mail"
perform action "AXRaise" of window t
delay 0.3
if name of front window is not t then error "compose window is not frontmost"
keystroke "w" using command down
end tell
end run'''
    osa(close, subject)
    html = next((p.get_content() for p in msg.walk() if p.get_content_type() == "text/html"), "")
    print(f"saved draft\nfrom={msg['From']}\nto={msg['To']}\nsubject={msg['Subject']}\n"
          f"urlshare_wrapper={'URLShare' in html}")


if __name__ == "__main__":
    main()
