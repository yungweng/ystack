# ystack

The agent skills I wrote and use every day. They work with Claude Code, Codex and
any other agent that reads the [Agent Skills](https://agentskills.io) format.

## Install

```console
npx skills add yungweng/ystack --global --skill '*'
```

Pick single skills with `--skill unknown-unknowns test-audit`, or list them first
with `npx skills add yungweng/ystack --list`. Update later with
`npx skills update --global`.

## Skills

### Thinking

| Skill | What it does |
| --- | --- |
| `unknown-unknowns` | Surfaces risks, constraints and questions you have not thought to ask |
| `extrapolate-knowledge` | Pushes what you already know into principles, predictions and next moves |
| `double-check-fact-check` | Verifies claims against primary sources and empirical checks |

### Engineering

| Skill | What it does |
| --- | --- |
| `test-audit` | Finds and removes low-value, duplicative or implementation-coupled tests |
| `pr-merge-prompt` | Turns a list of pull requests into a prompt for a sequential review and merge loop |
| `hill-climb-prompt-maker` | Writes optimization-loop prompts with baselines, verifiers and stopping rules |
| `canvas-animation` | Builds interactive canvas animations for React and Next.js sites |

### Writing

| Skill | What it does |
| --- | --- |
| `orwell-writing-rules` | Applies Orwell's rules to prose, docs, comments and commit messages |

### macOS

These read local app data and need macOS.

| Skill | What it does |
| --- | --- |
| `apple-mail-client` | Searches, reads, drafts and organizes mail in Apple Mail |
| `imessage` | Searches and sends iMessages and SMS |
| `whatsapp-search` | Searches the local WhatsApp message history |
| `audio-transcriber` | Transcribes audio files and voice notes locally with Whisper |
| `clipboard-copy` | Copies text to the system clipboard |

## The rest of my stack

`install.sh` installs ystack plus the third-party skills I use, for Claude Code
and Codex:

```console
curl -fsSL https://raw.githubusercontent.com/yungweng/ystack/main/install.sh | bash
```

| Source | Skills |
| --- | --- |
| [t3dotgg/tstack](https://github.com/t3dotgg/tstack) | all |
| [mattpocock/skills](https://github.com/mattpocock/skills) | all |
| [yungweng/wt](https://github.com/yungweng/wt) | `wt` |
| [vercel-labs/skills](https://github.com/vercel-labs/skills) | `find-skills` |
| [vercel-labs/agent-desktop](https://github.com/vercel-labs/agent-desktop) | `agent-desktop` |
| [yetone/kill-ai-slop](https://github.com/yetone/kill-ai-slop) | `kill-ai-slop` |
| [cloudflare/security-audit-skill](https://github.com/cloudflare/security-audit-skill) | `security-audit` |
| [latent-spaces/brag](https://github.com/latent-spaces/brag) | `brag`, `brag-slim` |
| [caldoai/skills](https://github.com/caldoai/skills) | `untangle-codebase` |

Third-party skills are installed from their own repositories at their current
version. Review them before use. `./install.sh --own-only` skips them.

## Development

Edit skills in a checkout and link them into the agent directory, so changes are
live and land in Git:

```console
git clone git@github.com:yungweng/ystack.git
ln -s "$PWD/ystack/skills/test-audit" ~/.claude/skills/test-audit
```
