"""Paging Engine for prosecode-heap-pager.

Computes the Retention Score for each historical conversation block and
classifies it as retain / page / evict. Emissions are appended to a
Liminate (.limn) session contract using a bounded 35-word vocabulary.

Stdlib only. No external dependencies.
"""

import argparse
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LIMN_VOCAB = {
    "add", "set", "to", "from",
    "retained-blocks", "paged-blocks", "evicted-blocks", "last-pager-pass",
    "block", "session", "contract", "open", "close", "begin", "end", "note",
    "retain", "page", "evict",
    "active", "resolved", "noise",
    "intent", "keyword", "score",
    "alpha", "beta", "delta", "turn", "similarity", "threshold",
    "pass", "pager", "true", "false",
}

_TOKEN_RE = re.compile(r"[a-z0-9_]+")


def tokenize(text):
    return _TOKEN_RE.findall(text.lower())


def keyword_similarity(block_tokens, intent_keywords):
    if not intent_keywords:
        return 0.0
    intent_set = {kw.lower() for kw in intent_keywords}
    block_set = set(block_tokens)
    hits = len(intent_set & block_set)
    return hits / len(intent_set)


def retention_score(similarity, delta_t, alpha, beta):
    recency = 1.0 / (1.0 + math.log(1 + delta_t))
    return alpha * similarity + beta * recency


def classify(score, retain_cut, evict_cut):
    if score >= retain_cut:
        return "retain"
    if score < evict_cut:
        return "evict"
    return "page"


_BUCKET = {
    "retain": "retained-blocks",
    "page": "paged-blocks",
    "evict": "evicted-blocks",
}


class LimnWriter:
    """Appends bounded Liminate statements to a .limn session contract."""

    def __init__(self, contract_path):
        self.path = Path(contract_path)

    def _emit(self, statement):
        for word in statement.replace('"', " ").split():
            if word.startswith('block-') or _is_quoted_id(word) or _is_iso_ts(word):
                continue
            if word not in LIMN_VOCAB:
                raise ValueError(f"vocabulary violation: {word!r} not in LIMN_VOCAB")
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(statement + "\n")

    def append_block(self, block_id, action):
        bucket = _BUCKET[action]
        self._emit(f'add "{block_id}" to {bucket}')

    def mark_pass(self, timestamp):
        self._emit(f"set last-pager-pass to {timestamp}")


def _is_quoted_id(word):
    return word.startswith("block-")


def _is_iso_ts(word):
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}t", word, re.IGNORECASE))


def run(history_path, contract_path, alpha, beta,
        retain_cut=0.55, evict_cut=0.20):
    history = json.loads(Path(history_path).read_text(encoding="utf-8"))
    intent = history["intent_ir"]
    head_turn = history.get("current_turn",
                            max(b["turn"] for b in history["blocks"]))
    writer = LimnWriter(contract_path)

    results = []
    for block in history["blocks"]:
        tokens = tokenize(block["text"])
        sim = keyword_similarity(tokens, intent)
        delta_t = head_turn - block["turn"]
        score = retention_score(sim, delta_t, alpha, beta)
        action = classify(score, retain_cut, evict_cut)
        writer.append_block(block["id"], action)
        record = {
            "block": block["id"],
            "kind": block.get("kind"),
            "similarity": round(sim, 4),
            "delta_t": delta_t,
            "R": round(score, 4),
            "action": action,
        }
        results.append(record)
        sys.stderr.write(json.dumps(record) + "\n")

    writer.mark_pass(datetime.now(timezone.utc).isoformat(timespec="seconds"))
    return {
        "alpha": alpha, "beta": beta,
        "retain_cut": retain_cut, "evict_cut": evict_cut,
        "results": results,
    }


def _summary(report):
    tally = {"retain": 0, "page": 0, "evict": 0}
    for r in report["results"]:
        tally[r["action"]] += 1
    print(f"alpha={report['alpha']} beta={report['beta']}  "
          f"retain={tally['retain']} page={tally['page']} evict={tally['evict']}")


def main(argv=None):
    p = argparse.ArgumentParser(description="prosecode-heap-pager engine")
    p.add_argument("--history", required=True)
    p.add_argument("--contract", required=True)
    p.add_argument("--alpha", type=float, default=0.7)
    p.add_argument("--beta", type=float, default=0.3)
    p.add_argument("--retain-cut", type=float, default=0.55)
    p.add_argument("--evict-cut", type=float, default=0.20)
    args = p.parse_args(argv)
    report = run(args.history, args.contract, args.alpha, args.beta,
                 args.retain_cut, args.evict_cut)
    _summary(report)


if __name__ == "__main__":
    main()
