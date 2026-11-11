---
name: clipboard-copy
description: Copy text to the system clipboard. Use when user asks to copy something to clipboard, copy to pasteboard, or wants to paste something.
---

# Copy to Clipboard

**Umlaut rule, never skip:** every `pbcopy` call needs `LANG=en_US.UTF-8`
directly on it, also when copying from another skill's flow or a one-off
command. Agent shells have no `LANG`, so a bare `pbcopy` turns „ü“ into „√º“.
After copying non-ASCII text, verify with
`osascript -e 'the clipboard as «class utf8»'` before reporting success.

When copying text to the clipboard on macOS, always use a heredoc with `pbcopy`. Never use `printf` or `echo` with escaped quotes as they break on apostrophes and special characters.

## Correct Method

```bash
cat << 'EOF' | LANG=en_US.UTF-8 pbcopy
Your text here with apostrophes like it's and don't.
Special characters work fine: é, ü, ñ, quotes "like this".
Multiple lines work too.
EOF
```

## Why Not printf or echo

```bash
# BAD - breaks on apostrophes, needs escaping, fragile
printf '%s' 'today'\''s meeting' | pbcopy

# BAD - same escaping problems
echo "He said \"hello\"" | pbcopy

# GOOD - heredoc with single-quoted delimiter preserves everything literally
cat << 'EOF' | LANG=en_US.UTF-8 pbcopy
today's meeting, "hello", it's all fine
EOF
```

## Key Rules

1. Always use `cat << 'EOF' | LANG=en_US.UTF-8 pbcopy` (single quotes around EOF to prevent variable expansion)
2. Never escape apostrophes or quotes manually
3. Works for any text: emails, code, prose, unicode
4. Always set `LANG=en_US.UTF-8` on `pbcopy`. Agent and GUI-launched shells often have no `LANG`; `pbcopy` then reads input as MacRoman and turns umlauts into `fÃ¼r`-style garbage (`f√ºr` when pasted).
5. Verify non-ASCII text after copying: `osascript -e 'the clipboard as «class utf8»'`
