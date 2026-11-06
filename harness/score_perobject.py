"""
score_perobject.py - offline rescorer for perobject_*.jsonl.

Rescoring never needs a re-run: every row carries answer, expect, tok_present and
the first 1500 chars of raw, so a scoring change is applied retroactively. This
script applies the leading-dot normalisation (a correct '.error_ledger.json'
written as 'error_ledger.json' was being counted as a swap) and reports:

  * arm x class, with answerable and trap questions separated. `answerable` means
    the evidence token was present in what that arm was shown, so a wrong answer
    is a real miss rather than a question the payload could not support.
  * misattribution = swap + fabrication. AMBIGUOUS is NOT a misattribution: the
    aggregator declined to pick, the model did not mis-bind.
  * sub-call level: what each individual call did when it saw k objects, and
    where its affirmatives landed.

usage:  python score_perobject.py perobject_gemma3-1b_<ts>.jsonl [more.jsonl ...]
"""
import json, sys, os, collections

CLS = ["correct", "refusal", "swap", "fabrication", "malformed", "ambiguous", "error"]
ARMS = ["guided", "pair_object", "per_object"]
K = {"guided": 6, "pair_object": 2, "per_object": 1}


def norm(s):
    return str(s).strip().lower().lstrip(".")


def rescore(r):
    """Leading-dot-normalised correctness; otherwise keep the recorded class."""
    if r["cls"] in ("ambiguous", "error"):
        return r["cls"]
    exp = {norm(e) for e in r["expect"].split("|")}
    return "correct" if norm(r["answer"]) in exp else r["cls"]


def report(path, out=sys.stdout):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    for r in rows:
        r["cls2"] = rescore(r)
    changed = sum(1 for r in rows if r["cls2"] != r["cls"])
    p = lambda *a: print(*a, file=out)
    p(f"\n=== {os.path.basename(path)}  ({len(rows)} rows, {changed} reclassified by "
      f"leading-dot normalisation) ===")
    p(f"{'arm':12} {'k':>2} {'n':>3} " + " ".join(f"{c[:5]:>6}" for c in CLS) +
      "    acc   answerable      trap   misattrib")
    for arm in ARMS:
        sub = [r for r in rows if r["arm"] == arm]
        if not sub:
            continue
        c = collections.Counter(r["cls2"] for r in sub)
        ansb = [r for r in sub if r["tok_present"]]
        trap = [r for r in sub if not r["tok_present"]]
        ok = lambda xs: sum(1 for r in xs if r["cls2"] == "correct")
        p(f"{arm:12} {K[arm]:>2} {len(sub):>3} " + " ".join(f"{c[x]:>6}" for x in CLS) +
          f"   {ok(sub)/len(sub):>4.0%}   {ok(ansb):>4}/{len(ansb):<4}  {ok(trap):>4}/{len(trap):<4}"
          f"   {c['swap']+c['fabrication']:>4}")
    p("\n-- sub-call level (one call, k objects in view) --")
    for arm in ("pair_object", "per_object"):
        sub = [r for r in rows if r["arm"] == arm + "_sub"]
        if not sub:
            continue
        c = collections.Counter(r["cls2"] for r in sub)
        p(f"{arm+'_sub':16} n={len(sub):<4} " + ", ".join(f"{x}={c[x]}" for x in CLS if c[x]))
    p("\n-- aggregate shape (n_affirmative, n_offlist) --")
    for arm in ("pair_object", "per_object"):
        sub = [r for r in rows if r["arm"] == arm]
        if sub and "n_affirmative" in sub[0]:
            p(f"{arm:12} " + str(dict(sorted(collections.Counter(
                (r["n_affirmative"], r["n_offlist"]) for r in sub).items()))))
    p("\n-- per-question, per-arm (correct count out of repeats) --")
    qids = list(dict.fromkeys(r["qid"] for r in rows))
    reps = max(r["rep"] for r in rows) + 1
    p(f"{'qid':14} " + " ".join(f"{a:>12}" for a in ARMS) + "   tok")
    for q in qids:
        cells = []
        for a in ARMS:
            s = [r for r in rows if r["arm"] == a and r["qid"] == q]
            cells.append(f"{sum(1 for r in s if r['cls2']=='correct')}/{len(s) or reps}")
        tok = any(r["tok_present"] for r in rows if r["qid"] == q and r["arm"] == "per_object")
        p(f"{q:14} " + " ".join(f"{c:>12}" for c in cells) + f"   {tok}")
    p("\n-- every non-correct question-level row --")
    for r in rows:
        if r["arm"] in ARMS and r["cls2"] != "correct":
            p(f"  {r['arm']:12} {r['qid']:14} rep{r['rep']} -> {r['answer']:22} "
              f"exp={r['expect']:24} {r['cls2']}")
    return rows


if __name__ == "__main__":
    for a in sys.argv[1:]:
        report(a)
