"""Benchmark harness for the prosecode-heap-pager engine.

Runs the pager across a matrix of (alpha, beta) ratios against
assets/test-history.json, asserts that:
  - every 'noise' block is evicted in the two intent-heavy alpha settings
  - every 'active' block is retained in every setting
  - no block is classified more than once per pass

Prints a formatted performance matrix to stdout. Exit 0 on full pass.
"""

import argparse
import io
import json
import sys
import tempfile
from contextlib import redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import pager  # noqa: E402

HISTORY = ROOT / "assets" / "test-history.json"
RATIOS = [(0.9, 0.1), (0.7, 0.3), (0.5, 0.5), (0.3, 0.7)]
INTENT_HEAVY = {(0.9, 0.1), (0.7, 0.3)}


def _run_one(alpha, beta, contract_path):
    buf = io.StringIO()
    with redirect_stderr(buf):
        report = pager.run(str(HISTORY), str(contract_path), alpha, beta)
    return report, buf.getvalue()


def _assert(report, kinds_by_id):
    seen = set()
    for r in report["results"]:
        if r["block"] in seen:
            raise AssertionError(f"double classification for {r['block']}")
        seen.add(r["block"])
        kind = kinds_by_id[r["block"]]
        if kind == "active" and r["action"] != "retain":
            raise AssertionError(
                f"active block {r['block']} not retained at "
                f"alpha={report['alpha']} (got {r['action']}, R={r['R']})"
            )
        if kind == "noise" and (report["alpha"], report["beta"]) in INTENT_HEAVY:
            if r["action"] != "evict":
                raise AssertionError(
                    f"noise block {r['block']} not evicted at "
                    f"alpha={report['alpha']} (got {r['action']}, R={r['R']})"
                )


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--verbose", action="store_true")
    args = ap.parse_args(argv)

    history = json.loads(HISTORY.read_text(encoding="utf-8"))
    kinds_by_id = {b["id"]: b["kind"] for b in history["blocks"]}

    print(f"{'alpha':>6} {'beta':>6}  {'retain':>6} {'page':>5} {'evict':>5}"
          f"  {'noise->evict':>13} {'active->retain':>15}")
    print("-" * 74)

    sample_contract = None
    for alpha, beta in RATIOS:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".limn", delete=False, dir=str(ROOT)
        ) as fh:
            contract_path = fh.name
        report, _ = _run_one(alpha, beta, contract_path)
        _assert(report, kinds_by_id)

        tally = {"retain": 0, "page": 0, "evict": 0}
        noise_evicted = active_retained = 0
        noise_total = active_total = 0
        for r in report["results"]:
            tally[r["action"]] += 1
            k = kinds_by_id[r["block"]]
            if k == "noise":
                noise_total += 1
                if r["action"] == "evict":
                    noise_evicted += 1
            if k == "active":
                active_total += 1
                if r["action"] == "retain":
                    active_retained += 1

        print(f"{alpha:>6.2f} {beta:>6.2f}  "
              f"{tally['retain']:>6} {tally['page']:>5} {tally['evict']:>5}"
              f"  {noise_evicted:>6}/{noise_total:<6} "
              f"{active_retained:>7}/{active_total:<7}")

        if args.verbose:
            for r in report["results"]:
                print(f"    {r['block']}  kind={kinds_by_id[r['block']]:<8} "
                      f"sim={r['similarity']:.3f} dt={r['delta_t']:>2} "
                      f"R={r['R']:.4f} -> {r['action']}")

        if sample_contract is None:
            sample_contract = contract_path
        else:
            Path(contract_path).unlink()

    print("\nAll assertions passed.")
    print(f"Sample .limn contract: {sample_contract}")


if __name__ == "__main__":
    main()
