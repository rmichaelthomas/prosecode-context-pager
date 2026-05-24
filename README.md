# prosecode-context-pager

Decides which parts of a long conversation an agent should keep, summarize, or throw away.

*Part of the Prosecode family — a set of tools for writing, verifying, and transferring structured reasoning.*

It reads the chat history one block at a time, scores each block against what the agent is currently trying to do, and writes the decision into a [session contract](https://github.com/rmichaelthomas/liminate-session-contracts) so the next pass knows what was kept and what was let go.

## What it does

For every historical block in the active window the pager picks one of three actions:

| Directive | What happens to the block | What kind of block |
|---|---|---|
| `retain` | Stays in the active context, untouched. | Current goals, open questions, the slot values the agent is still working with. |
| `page` | Gets replaced by a short summary stub. The full text moves out of the live window but can be pulled back. | Resolved sub-tasks, older analytical passages, closed arguments. |
| `evict` | Removed from the stream. | Typos that were corrected, syntax errors that were fixed, raw logs whose findings have already been written down. |

The decision is deterministic. Same history, same intent, same score, same action. Nothing is dropped silently — every action becomes a line in the session contract.

## Example

```
add "block-0x07" to evicted-blocks
add "block-0x04" to paged-blocks
add "block-0x01" to retained-blocks
set last-pager-pass to 2026-05-17T03:08:12+00:00
```

The pager emits Liminate statements only. Every emitted line is checked against the bounded 35-word vocabulary before it is appended, so a vocabulary slip fails loudly instead of producing a malformed contract.

## Built by Liminate

Liminate is a prose-as-syntax language where plain English sentences execute directly. These five repos form a system for writing, verifying, and transferring structured reasoning.

| | Repo | What it does |
|---|---|---|
| | [liminate](https://github.com/rmichaelthomas/liminate) | The language and interpreter. Bounded vocabulary, deterministic execution, domain packs. |
| | [liminate-session-contracts](https://github.com/rmichaelthomas/liminate-session-contracts) | Tracks verified sources, inferred claims, locked decisions, and user corrections as executable `.limn` contracts. |
| | [prosecode-prompt-compiler](https://github.com/rmichaelthomas/prosecode-prompt-compiler) | Compiles user prompts into structured intent before the agent responds. Seven verbs, twenty-four slots. |
| **← this repo** | [**prosecode-context-pager**](https://github.com/rmichaelthomas/prosecode-context-pager) | **Scores conversation history against current intent. Decides what to keep, summarize, or drop.** |
| | [prosecode-handoff-packet](https://github.com/rmichaelthomas/prosecode-handoff-packet) | Packages a working session for another agent to continue — preserving what was verified and what wasn't. |

→ [liminate.dev](https://liminate.dev)

## Install

This skill follows the [agentskills.io](https://agentskills.io) SKILL.md standard. Any compliant agent can load it.

```bash
# Claude Code — all projects
git clone https://github.com/rmichaelthomas/prosecode-context-pager.git ~/.claude/skills/prosecode-context-pager

# Claude Code — one project
git clone https://github.com/rmichaelthomas/prosecode-context-pager.git .claude/skills/prosecode-context-pager

# Codex CLI
git clone https://github.com/rmichaelthomas/prosecode-context-pager.git ~/.codex/skills/prosecode-context-pager

# Gemini CLI
git clone https://github.com/rmichaelthomas/prosecode-context-pager.git ~/.gemini/skills/prosecode-context-pager

# Any SKILL.md-compatible agent
git clone https://github.com/rmichaelthomas/prosecode-context-pager.git .agents/skills/prosecode-context-pager
```

There is nothing to `pip install`. The engine is Python 3 standard library only — no tokenizers, no ML packages, no network calls.

The Liminate interpreter is optional. Install it if you want the agent to validate the contract as it writes:

```bash
pip install liminate
liminate path/to/session-contract.limn
```

## How it works

### As a skill

Once the repo is on your skill path, ask the agent to run a paging pass when the context starts feeling heavy:

> "Page the context against the current intent before we keep going."

Good moments to run it: right after the prompt compiler resolves a new instruction, when the conversation crosses several distinct task iterations, and before any handoff that writes a final artifact.

### As a standalone CLI

You can also run the engine directly against a JSON history file:

```bash
python3 scripts/pager.py \
  --history assets/test-history.json \
  --contract /tmp/session-contract.limn \
  --alpha 0.7 --beta 0.3
```

What the flags do:

- `--history` — a JSON file with an `intent_ir` keyword list and a list of `blocks`. See `assets/test-history.json` for the schema.
- `--contract` — the `.limn` file to append decisions to. Created if it does not exist.
- `--alpha`, `--beta` — weights for the retention score.
- `--retain-cut`, `--evict-cut` — score thresholds, default `0.55` and `0.20`.

The CLI prints a one-line summary to stdout and a structured JSON record for every block to stderr.

### How the score works

Each block gets a retention score `R`:

```
R = alpha * similarity + beta * (1 / (1 + ln(1 + delta_t)))
```

- `similarity` is the fraction of the active intent keywords that appear in the block. Native string tokenization, no embeddings.
- `delta_t` is how many turns ago the block was written.
- `alpha` weights relevance. `beta` weights recency. They do not have to sum to 1, but the defaults `0.7` and `0.3` are a good starting point.

`R >= retain-cut` is kept. `R < evict-cut` is dropped. Anything in between is paged.

The formula is deliberately boring. Readable, predictable, tunable without machine learning.

### Liminate vocabulary gate

The pager only writes statements that fit inside Liminate's bounded 35-word vocabulary. The full set lives in `LIMN_VOCAB` at the top of `scripts/pager.py`. Every emitted statement is validated against that set before it is appended.

### Benchmark

```bash
python3 scripts/benchmark-pager.py --verbose
```

Runs the engine against `assets/test-history.json` across four `(alpha, beta)` ratios and asserts the invariants that matter: every `active` block ends up `retain`, every `noise` block ends up `evict` under the intent-heavy settings, and no block is classified twice in a single pass. Exits 0 on a clean pass and prints a matrix of how many blocks landed in each bucket per ratio.

### Repository structure

```text
prosecode-context-pager/
├── SKILL.md                     # Agent-facing protocol (agentskills.io frontmatter)
├── README.md
├── references/
│   └── paging-directives.md     # Formal spec for retain / page / evict
├── assets/
│   └── test-history.json        # Synthetic 12-block session used by the benchmark
└── scripts/
    ├── pager.py                 # The engine, plus a CLI
    └── benchmark-pager.py       # Runs the engine across an (alpha, beta) matrix
```

## License

MIT
