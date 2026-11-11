#!/usr/bin/env bash
# Install ystack and the third-party skills listed in README.md, globally,
# for Claude Code and Codex. Requires Node.js (npx).
#
#   ./install.sh             ystack plus third-party skills
#   ./install.sh --own-only  ystack only
set -euo pipefail

AGENTS=(claude-code codex)

# add REPO SKILL...   ('*' installs every skill of the repository)
# --copy: symlinks from the shared skills directory break when the agent's
# skills directory is itself a symlink (for example a Stow checkout).
add() {
    local repo=$1
    shift
    printf '\n== %s\n' "$repo"
    npx --yes skills add "$repo" --global --agent "${AGENTS[@]}" --skill "$@" --copy --yes
}

if ! command -v npx >/dev/null 2>&1; then
    echo "npx not found. Install Node.js first." >&2
    exit 1
fi

add yungweng/ystack '*'

if [[ "${1:-}" == "--own-only" ]]; then
    exit 0
fi

add t3dotgg/tstack '*'
add mattpocock/skills '*'
add yungweng/wt wt
add vercel-labs/skills find-skills
add vercel-labs/agent-desktop agent-desktop
add yetone/kill-ai-slop kill-ai-slop
add cloudflare/security-audit-skill security-audit
add latent-spaces/brag brag brag-slim
add caldoai/skills untangle-codebase
