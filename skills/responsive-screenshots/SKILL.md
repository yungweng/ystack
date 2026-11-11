---
name: responsive-screenshots
description: Use when a frontend change needs a responsiveness check across device sizes. Captures every relevant view on iPhone SE, iPhone 12, iPhone 16 Pro Max, iPad Air, iPad Pro and desktop with agent-browser. Triggers on "responsiveness", "mobile check", "alle Auflösungen", "device sweep", or before merging UI work that touches layout.
---

# Responsive Screenshot Sweep

Capture every relevant view of an app at the six canonical viewports so
layout breaks (overflow, truncation, stacked controls, hidden context) become
visible before review. Output: one PNG per route × viewport plus an overflow
report.

Requires the [agent-browser](https://github.com/vercel-labs/agent-browser) CLI.

## Viewports (logical CSS pixels)

| Tag    | Device            | Size      |
|--------|-------------------|-----------|
| `se`   | iPhone SE         | 375×667   |
| `12p`  | iPhone 12 / Pro   | 390×844   |
| `16pm` | iPhone 16 Pro Max | 430×932   |
| `air`  | iPad Air          | 820×1180  |
| `pro`  | iPad Pro 12.9"    | 1024×1366 |
| `dt`   | Desktop           | 1440×900  |

375 is the floor: what survives `se` survives everything. Tablets catch the
`md:`/`lg:` breakpoint seams (sidebar vs bottom nav, grid column switches).

## Prerequisites

- The app runs locally with seeded test data. Use the project's local test
  logins; never copy credentials into the report, logs or screenshots.
- Log in once via the UI and keep the agent-browser daemon alive. Short-lived
  sessions expire mid-sweep, and the sweep then silently lands on the login
  page (see gotchas).
- Build the route list from the app's navigation (snapshot the nav, sidebar and
  overflow menus and collect hrefs), including detail pages (`/items/1`), not
  just top-level tabs.

## Sweep script pattern

```bash
S=<scratchpad>/shots; mkdir -p $S
routes="/:home /items:list /items/1:detail ..."
for vp in "375 667 se" "390 844 12p" "430 932 16pm" "820 1180 air" "1024 1366 pro" "1440 900 dt"; do
  read w h tag <<< "$vp"
  agent-browser set viewport $w $h >/dev/null
  for r in $routes; do
    path=${r%%:*}; name=${r##*:}
    agent-browser open "http://<host>$path" >/dev/null 2>&1
    agent-browser wait --load networkidle >/dev/null 2>&1; sleep 1
    agent-browser screenshot --full "$S/$name-$tag.png" >/dev/null 2>&1
    ow=$(agent-browser eval "document.documentElement.scrollWidth" | tr -d '"')
    [ "$ow" -gt "$w" ] 2>/dev/null && echo "OVERFLOW $name-$tag: $ow > $w"
  done
done
```

The `scrollWidth > viewport` probe is the payoff: it catches horizontal
overflow objectively, even when the screenshot "looks fine" at a glance.
To find the offending element, iterate `querySelectorAll('*')` and report
nodes whose `getBoundingClientRect().right` exceeds the viewport width.

## Gotchas (all hit in practice)

- **Session expiry mid-sweep**: once the session expires, every screenshot is
  the login page. Detect it via identical file sizes across routes (`ls -la` —
  same byte count for different routes = same page). Re-login and retake only
  those files.
- **Fullpage screenshots lie about fixed elements**: `screenshot --full`
  renders `position: fixed` chrome (bottom nav) at its viewport position,
  mid-page. An apparent overlap there is an artifact — verify live by
  scrolling to the element and checking `getBoundingClientRect()` against the
  nav before filing a bug.
- **Dev servers fall over mid-sweep**: a containerized dev server can
  crash-loop while compiling routes on demand. If pages return 500 or refuse
  the connection, check the server and retake with retries. A dev server run
  directly on the host is steadier for long sweeps.
- **Dedicated session for parallel work**: `agent-browser --session <name>`;
  the default session is shared across concurrent agent sessions, which can
  swap your login or tab out from under you.
- **A `grid gap-* lg:grid-cols-2` without `grid-cols-1`** is the classic
  overflow root cause the probe finds: below the breakpoint the implicit auto
  column grows to max-content and `truncate` stops working.

## Delivery: post the sweep as a PR comment via gh

Read the worst-viewport (`se`) shots yourself and fix what they show. Then
publish the sweep on the PR as native attachments; local file paths alone are
not a delivery.

```bash
# comment.md references every shot by its local path: ![iPhone SE – Overview](<shots>/home-se.png)
gh pr comment <NR> --body-file comment.md $(printf -- '--attach %s ' <shots>/*.png)
```

Structure the comment: before/after pairs first (if any), then one collapsed
`<details>` block per viewport with all views. Short caption above every image.

**Re-running the sweep? Update, don't stack comments**: rerun the same command
with `--edit-last`.

For before/after pairs of a specific change use the `ui-before-after` skill —
this skill is the breadth sweep, that one is the depth comparison.
