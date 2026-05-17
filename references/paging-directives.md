# Paging Directives

The Paging Engine emits one of three directives per historical block.
The directive is chosen from the block's Retention Score `R`:

```
R = alpha * similarity + beta * (1 / (1 + ln(1 + delta_t)))
```

`similarity` is the keyword-weight intersection between the block and the
active Intent IR. `delta_t` is the turn distance between the block and the
current head of the session.

## retain

- **Triggers:** active targets, open questions, currently-bound Intent IR slots.
- **Score range:** `R >= retain_cut` (default `0.55`).
- **Liminate verb:** `add "<block-id>" to retained-blocks`
- **Effect:** block remains inline in the active context window.

## page

- **Triggers:** resolved sub-tasks, older analytical passages, summaries of
  closed loops still useful as reference.
- **Score range:** `evict_cut <= R < retain_cut` (default `0.20 <= R < 0.55`).
- **Liminate verb:** `add "<block-id>" to paged-blocks`
- **Effect:** full text is replaced with a short stub; original moved to the
  paged store and recallable on demand.

## evict

- **Triggers:** syntax errors, corrected typos, fully compiled raw material
  whose distilled form is already retained.
- **Score range:** `R < evict_cut` (default `R < 0.20`).
- **Liminate verb:** `add "<block-id>" to evicted-blocks`
- **Effect:** hard removal; the block is not recoverable from the session
  contract.

## Pass marker

After every full pass the engine writes:

```
set last-pager-pass to <iso-timestamp>
```

All emitted statements stay inside the Liminate 35-word vocabulary defined in
`scripts/pager.py::LIMN_VOCAB`.
