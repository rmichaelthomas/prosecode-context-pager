# prosecode-heap-pager

A skill that decides which parts of a long conversation an LLM should keep, summarize, or throw away.

It reads the chat history one block at a time, scores each block against what the agent is currently trying to do, and writes the decision into a [session contract](https://github.com/rmichaelthomas/session-contracts) so the next pass knows what was kept and what was let go.

## What it does

For every historical block in the active window the pager picks one of three actions:

| Directive | What happens to the block | What kind of block |
| --- | --- | --- |
| `retain` | Stays in the active context, untouched. | Current goals, open questions, the slot values the agent is still working with. |
| `page` | Gets replaced by a short summary stub. The full text is moved out of the live window but can be pulled back. | Resolved sub-tasks, older analytical passages, closed arguments. |
| `evict` | Removed from the stream. | Typos that were corrected, syntax errors that were fixed, raw logs whose findings have already been written down. |

The decision is deterministic. Same history, same intent, same score, same action. Nothing is dropped silently — every action becomes a line in the session contract.

## Why it exists

Long sessions go bad in a predictable way. The window fills up, attention spreads thin, old typos and dead debug loops start competing with the live work, and the model drifts. The usual fixes are blunt — truncate the oldest N tokens, or compress everything that scrolled past some line.

This skill does something narrower. It keeps what the agent is actually using right now, summarizes what mattered a few turns ago, and removes what was never going to matter again. The choice is per block, not per range, and it is recorded.

It is one of three pieces that work together:

- [`prosecode-intent-compiler`](https://github.com/rmichaelthomas/prosecode-intent-compiler) — reads the user's prompt and produces a small Intent IR (verb plus slots).
- `prosecode-heap-pager` — uses that IR to score and prune the history.
- [`session-contracts`](https://github.com/rmichaelthomas/session-contracts) — the file the pager writes into, in [Liminate](https://github.com/rmichaelthomas/liminate).

You can use the pager on its own. The other two make it more useful.

## Install

This skill follows the [agentskills.io](https://agentskills.io) SKILL.md standard. Any compliant agent can load it.

```bash
# Claude Code — all projects
git clone https://github.com/rmichaelthomas/prosecode-heap-pager.git ~/.claude/skills/prosecode-heap-pager

# Claude Code — one project
git clone https://github.com/rmichaelthomas/prosecode-heap-pager.git .claude/skills/prosecode-heap-pager

# Codex CLI
git clone https://github.com/rmichaelthomas/prosecode-heap-pager.git ~/.codex/skills/prosecode-heap-pager

# Gemini CLI
git clone https://github.com/rmichaelthomas/prosecode-heap-pager.git ~/.gemini/skills/prosecode-heap-pager

# Any SKILL.md-compatible agent
git clone https://github.com/rmichaelthomas/prosecode-heap-pager.git .agents/skills/prosecode-heap-pager
```

There is nothing to `pip install`. The engine is Python 3 standard library only — no tokenizers, no ML packages, no network calls.

The Liminate interpreter is optional. Install it if you want the agent to validate the contract as it writes:

```bash
pip install liminate
liminate path/to/session-contract.limn
```

## Use

### As a skill

Once the repo is on your skill path, ask the agent to run a paging pass when the context starts feeling heavy:

> "Page the heap against the current intent before we keep going."

The agent will profile the history, score each block, and append the actions to the session contract as Liminate statements such as:

```
add "block-0x07" to evicted-blocks
add "block-0x04" to paged-blocks
add "block-0x01" to retained-blocks
set last-pager-pass to 2026-05-17T03:08:12+00:00
```

Good moments to run it: right after the intent compiler resolves a new instruction, when the conversation crosses several distinct task iterations, and before any handoff that writes a final artifact.

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
- `--alpha`, `--beta` — weights for the retention score. See below.
- `--retain-cut`, `--evict-cut` — score thresholds, default `0.55` and `0.20`.

The CLI prints a one-line summary to stdout and a structured JSON record for every block to stderr.

## How the score works

Each block gets a retention score `R`:

```
R = alpha * similarity + beta * (1 / (1 + ln(1 + delta_t)))
```

- `similarity` is the fraction of the active intent keywords that appear in the block. Native string tokenization, no embeddings.
- `delta_t` is how many turns ago the block was written.
- `alpha` weights relevance. `beta` weights recency. They do not have to sum to 1, but the defaults `0.7` and `0.3` are a good starting point.

`R >= retain-cut` is kept. `R < evict-cut` is dropped. Anything in between is paged.

The formula is deliberately boring. It is meant to be readable, predictable, and tunable without machine learning.

## Repository structure

```text
prosecode-heap-pager/
├── SKILL.md                     # Agent-facing protocol (agentskills.io frontmatter)
├── README.md                    # This file
├── references/
│   └── paging-directives.md     # Formal spec for retain / page / evict
├── assets/
│   └── test-history.json        # Synthetic 12-block session used by the benchmark
└── scripts/
    ├── pager.py                 # The engine, plus a CLI
    └── benchmark-pager.py       # Runs the engine across an (alpha, beta) matrix
```

## Benchmark

The benchmark runs the engine against `assets/test-history.json` across four `(alpha, beta)` ratios and asserts the invariants that matter: every `active` block ends up `retain`, every `noise` block ends up `evict` under the intent-heavy settings, and no block is classified twice in a single pass.

```bash
python3 scripts/benchmark-pager.py --verbose
```

Exits 0 on a clean pass and prints a matrix of how many blocks landed in each bucket per ratio. Use it as a regression check whenever you change the scoring code.

## Liminate vocabulary

The pager only writes statements that fit inside Liminate's bounded 35-word vocabulary. The full set lives in `LIMN_VOCAB` at the top of `scripts/pager.py`. Every emitted statement is validated against that set before it is appended, so a vocabulary slip fails loudly instead of producing a malformed contract.

## License

MIT
