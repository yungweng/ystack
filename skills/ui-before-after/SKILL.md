---
name: ui-before-after
description: Use when a UI change needs before/after screenshot pairs for a PR or review. Triggers on "vorher/nachher", "before/after screenshots", visual comparison of a frontend refactor, or verifying that a migration did not change the look.
---

# Before/After UI Screenshot Pairs

Capture the same interactions against two pinned source states, verify the
rendered state before each screenshot, and composite matched pairs.
Bundlers such as Turbopack can serve stale modules after a source switch. Hot
reload alone does not establish which state the browser shows.

Requires the [agent-browser](https://github.com/vercel-labs/agent-browser) CLI
and ImageMagick. Examples assume a Next.js app whose build cache is `.next`;
substitute your framework's dev command and cache directory.

## Prerequisites

- Start from a clean working tree with the UI changes committed. Record the
  original branch/commit and pin the baseline to a commit with `git rev-parse`.
  Keep unrelated changes and untracked files intact; if they overlap the paths
  to switch, use a separate prepared checkout instead of overwriting them.
- Record the actual frontend start command, mode, port, working directory and
  process ownership before switching sources. If another task uses this source
  tree or the frontend cannot be restarted safely, move the comparison into a
  separate prepared checkout with its own port and cache **before any switch**.
  Use the existing mode throughout. Start only the services the shot list
  needs; preserve the database.
- Use the project's local test logins, without copying them into
  documentation, logs or screenshots.
- Use a dedicated `agent-browser --session <name>` session. Capture each changed
  surface at **desktop (1440×900)** and **mobile (390×844)**. Before reproducing
  the interactions at each size, set `agent-browser --session s set viewport
  1440 900` or `agent-browser --session s set viewport 390 844` respectively.
  Match dimensions within each before/after pair; prefix filenames with
  `desktop-` or `mobile-` so both pairs remain identifiable.

## Source-state gate (every switch, including final restoration)

1. **Stop the dev server, clear its build cache, then restart it** after the
   target sources are on disk. Do this after **every** switch: baseline, branch
   and final restoration. Use the recorded command, mode and port each time.
   - Stop only task-owned processes after checking their command and checkout.
     Never kill a listener just because it occupies the desired port.
   - Confirm the old listener has exited before removing the cache.
   - Verify the cache directory is not a symlink or a cache shared with another
     checkout, then remove it:
     ```bash
     test ! -L .next && rm -rf -- .next
     ```
   - Start the replacement on the same port with the same environment.
   - If ownership has changed since preflight, return to the prerequisites and
     isolate the checkout before continuing.

   Restart **and** fresh cache are required; hot reload or a browser reload
   does not replace either step. Never delete shared caches or data.
2. **Check the rendered target, not just server readiness.** Open the URL, wait
   for the expected page/interaction state, then take a fresh snapshot. For a
   visible change, assert the target-specific text, styling or element and the
   absence of the other state's distinguishing feature. Inspect the image when
   appearance, rather than text, is the distinction.
   For example, adapt this DOM assertion to the shot's real selector and texts:
   ```bash
   agent-browser --session s wait --fn 'document.querySelector("h1")?.innerText === "Expected target heading" && !document.body.innerText.includes("Other state heading")'
   ```
   Require a successful assertion before running `screenshot`; a timeout or
   mismatch blocks that shot. Record the assertion and observed value.
   For claimed visual equality, use an explicit target-specific rendered marker
   tied to the pinned commit (a temporary verification-only label outside the
   comparison region, recorded separately). Remove it during final restoration;
   never commit it as product code. A startup message, fixed sleep, browser
   reload, successful HTTP response or clean Git status alone is not proof.
3. **Record evidence**: expected ref/commit, switched paths, restart/reset command,
   old/new process identity, URL, rendered assertion and screenshot filename.
   Apply the rendered check before **each** screenshot, after reproducing its
   interactions. If the expected state cannot be established, stop capturing
   and investigate; do not label the image as before/after.

## Workflow

1. **Plan the shot list.** List URLs, exact interactions and required data for
   each surface and viewport. Choose a rendered-state assertion for each target
   before switching. Create needed data once; use the same data and interactions
   throughout both passes, matching the viewport within each pair.
2. **BEFORE:** restore only the comparison paths from the pinned baseline into
   the working tree, leaving the index at the branch state:
   ```bash
   git restore --source=<baseline-sha> --worktree -- <ui-source-paths>
   ```
   Inspect added/deleted paths too: branch-only files must not leak into the
   baseline. If dependencies or configuration differ, include those inputs in
   the plan or use isolated checkouts; swapping the source directory alone is
   not equivalent.
   Run the source-state gate, then walk the shot list at **both viewports**.
   Set the size before opening the URL and reproducing its interactions; take
   fresh refs after resizing. Use `desktop` or `mobile` for `<viewport>`:
   ```bash
   agent-browser --session s open <url>
   agent-browser --session s snapshot -i -c
   agent-browser --session s click @eN
   # Re-snapshot and verify the target-specific rendered assertion here.
   agent-browser --session s screenshot shots/before/<viewport>-<nn>-<name>.png
   ```
3. **AFTER:** restore the comparison paths from the recorded branch commit:
   ```bash
   git restore --source=<branch-sha> --worktree -- <ui-source-paths>
   ```
   Run the source-state gate again. Repeat the same URLs and interactions at
   **both viewports**, verifying the branch assertion before each image. Use
   identical viewport-prefixed filenames under `shots/after/`.
4. **Composite pairs** with ImageMagick, left=before and right=after. Use a
   task-owned output directory and unique temporary filenames:
   ```bash
   for f in shots/before/*.png; do
     n=$(basename "$f")
     magick "$f" -resize 50% -bordercolor gray -border 1 "shots/b-$n"
     magick "shots/after/$n" -resize 50% -bordercolor gray -border 1 "shots/a-$n"
     magick "shots/b-$n" "shots/a-$n" +append "shots/pair-$n"
   done
   ```
5. **Restore even after failure.** Remove only task-created verification markers
   and restore all switched paths to the original branch commit. Run the same
   source-state gate one last time and verify the original UI is rendered and
   temporary markers are absent. Check `git status --short` against the initial
   state as a separate source check. Then close the dedicated browser session
   and stop task-owned services no longer needed. Preserve pre-existing
   services, databases, volumes and caches; record anything left running.
6. **Deliver** the inspected pairs with the ref/restart/rendered evidence, posted
   on the PR as native attachments:
   ```bash
   gh pr comment <NR> --body-file comment.md $(printf -- '--attach %s ' shots/pair-*.png)
   ```

## Interaction notes

- Browser element refs go stale after navigation or re-render. Take a fresh
  `snapshot -i -c` before interacting; a reported successful fill is not proof
  the expected state was reached.
- Capture menus/popovers open, then press Escape before navigating onward.
- Empty states are often reachable by searching gibberish (`xyznothing`).
- Keep data unchanged between passes. Relative timestamps may differ; record
  that limitation rather than altering records to make the images match.
