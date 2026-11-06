"""run_ledger.py - every model run this project has ever done, derived from disk.

The problem this solves: in a long session, context compaction folds earlier
spans into summaries, and the agent asks for a run that was already done months
or hours ago. The user pays for it twice. Memory does not fix this - memory is
keyword-matched and fragmentary. Evidence does.

So this reads the RESULT FILES THEMSELVES - their parameters, modification
dates, call counts and headline numbers - and emits one table. It remembers
nothing. If a run happened, its output is on disk and it appears here; if it
does not appear here, it did not happen.

RULE FOR ANY AGENT ON THIS PROJECT: read RUN_LEDGER.md before proposing a run.

Model-free, offline, safe to re-run.
usage:  python run_ledger.py        -> RUN_LEDGER.md
"""
import os, re, sys, json, glob, time

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
RECORDS = os.environ.get("FIT_RECORDS", os.path.join(PKG, "records"))
RESULTS = os.environ.get("FIT_RESULTS", os.path.join(PKG, "results"))
MEASUREMENTS = os.environ.get("FIT_MEASUREMENTS", os.path.join(PKG, "measurements"))
CORPUS = os.environ.get("FIT_CORPUS") or next(
    (p for p in (os.path.join(PKG, "replica"),
                 os.path.join(PKG, "corpus_fixture")) if os.path.isdir(p)),
    os.path.join(PKG, "corpus_fixture"))


def jload(p):
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def count_lines(p):
    try:
        with open(p, encoding="utf-8", errors="replace") as fh:
            return sum(1 for l in fh if l.strip())
    except Exception:
        return 0


def when(p):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(p)))


def main():
    rows = []

    # ---- attenuation runs -----------------------------------------------
    for p in sorted(glob.glob(os.path.join(RECORDS, "attenuate_*.json"))):
        b = os.path.basename(p)
        if ".bak." in b or b.endswith(".jsonl"):
            continue
        d = jload(p)
        if not isinstance(d, dict):
            continue
        raw = p[:-5] + ".jsonl"
        n = count_lines(raw) if os.path.exists(raw) else 0
        hit = d.get("hit", {}); fa = d.get("fa", {})
        head = (f"citation {hit.get('span_verified','?')}/{hit.get('n','?')}, "
                f"swaps {fa.get('swaps','?')}/{fa.get('n','?')}, "
                f"refused {fa.get('refused','?')}")
        note = ""
        if d.get("rescored_with_evidence"):
            r = d["rescored_with_evidence"]
            head = (f"RESCORED: citation {r['hit']['citation_verified']}/16, "
                    f"swaps caught {r['fa']['caught_by_evidence_check']}/16, "
                    f"false-affirm {r['fa']['effective_false_affirm']}")
        elif "_lines" in b:
            note = "SUMMARY UNRELIABLE - see D9; use the _rescored file"
        rows.append(dict(kind="attenuate", model=d.get("model", "?"),
                         variant=d.get("prompt_variant", "?"), seed=d.get("seed"),
                         nq=d.get("n_questions"), calls=n, mins=d.get("elapsed_min"),
                         secs=d.get("median_secs"), errors=d.get("errors"),
                         when=when(p), file=b, head=head, note=note))

    # ---- envelopes (calibration runs) -----------------------------------
    for p in sorted(glob.glob(os.path.join(RESULTS, "envelope_*.json"))):
        b = os.path.basename(p)
        if ".bak." in b:
            continue
        d = jload(p)
        if not isinstance(d, dict):
            continue
        rec = d.get("recommend", {}) or {}
        sel = d.get("selection", {}) or {}
        head = (f"separation {d.get('separation', rec.get('separation', '?'))}, "
                f"window {rec.get('max_bytes_per_object','?')}, "
                f"verifier {rec.get('usable_as_verifier', rec.get('verification','?'))}")
        rows.append(dict(kind="calibrate", model=d.get("model", b),
                         variant="envelope", seed=d.get("seed"),
                         nq=d.get("requested_n") or d.get("n_questions"),
                         calls=d.get("n_calls"), mins=None, secs=d.get("median_secs"),
                         errors=d.get("errors"), when=when(p), file=b,
                         head=head, note=""))

    # ---- everything else that is a saved raw record ---------------------
    for p in sorted(glob.glob(os.path.join(RECORDS, "*.jsonl"))):
        b = os.path.basename(p)
        if b.startswith("attenuate_") or ".bak." in b:
            continue
        rows.append(dict(kind="raw", model="-", variant=b.replace(".jsonl", ""),
                         seed=None, nq=None, calls=count_lines(p), mins=None,
                         secs=None, errors=None, when=when(p), file=b,
                         head=f"{count_lines(p)} recorded calls", note=""))

    rows.sort(key=lambda r: r["when"])
    total = sum(r["calls"] or 0 for r in rows)

    out = ["# Run ledger - every model run on disk\n",
           f"Rebuilt {time.strftime('%Y-%m-%d %H:%M')} by `run_ledger.py` from the result",
           "files themselves. It remembers nothing: if a run is not here, its output is",
           "not on disk. **Read this before proposing any run.**\n",
           f"**{len(rows)} runs · {total} recorded model calls.**\n",
           "| when | kind | model | variant | seed | n | calls | s/call | headline |",
           "|---|---|---|---|---|---|---|---|---|"]
    for r in rows:
        out.append(f"| {r['when']} | {r['kind']} | `{r['model']}` | {r['variant']} | "
                   f"{r['seed'] if r['seed'] is not None else '-'} | "
                   f"{r['nq'] or '-'} | {r['calls'] or '-'} | "
                   f"{r['secs'] or '-'} | {r['head']} |")
    flagged = [r for r in rows if r["note"]]
    if flagged:
        out.append("\n## Flagged - do not quote these summaries\n")
        for r in flagged:
            out.append(f"- `{r['file']}` - {r['note']}")
    out.append("\n## Not on disk, therefore not run\n")
    out.append("Anything absent from the table above. Check here before asking the")
    out.append("user to run something - the cost of a forgotten run is paid twice.")
    md = "\n".join(out) + "\n"
    open(os.path.join(MEASUREMENTS, "RUN_LEDGER.md"), "w", encoding="utf-8").write(md)
    print(f"[ok] RUN_LEDGER.md - {len(rows)} runs, {total} recorded calls")
    for r in rows:
        print(f"   {r['when']}  {r['kind']:<9} {r['model']:<14} {r['variant']:<10} "
              f"{str(r['calls'] or '-'):>5} calls")


if __name__ == "__main__":
    main()
