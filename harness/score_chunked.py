"""
score_chunked.py - offline scorer for chunked_*.jsonl (measurement 7).

The two-pass arm logs pass 1 (select, over the descriptor index) and pass 2
(verify, over the selected file's windows) as SEPARATE rows, so the aggregation
rule is a scoring decision rather than a property of the run. Three rules are
scored from the same rows, no re-run:

  strict    final = pass-1 pick only if pass 2 re-affirms it, else NONE.
            This is what probe_chunked.py printed live. It assumes a NONE from
            pass 2 is evidence of absence.
  lenient   pass 2 vetoes only by NAMING A DIFFERENT FILE. A NONE from pass 2 is
            treated as no information, not as a veto -- which is what measurement
            6 says it is at 1B, where the k=1 hit rate is 8/18 (0/6 on
            subsystem_daemon.py).
  pass1     final = the pass-1 pick. The index selection standing on its own, with
            no verification at all.

Reading the three together answers a question worth more than the original one:
how much verification can a model of this size actually be trusted to do?

Also reports pair_shuffled per seed, which is the de-confound for measurement 6's
k=2 headline.

usage:  python score_chunked.py chunked_gemma3-1b_<ts>.jsonl [more ...]
"""
import json, sys, os, collections

CLS = ["correct", "refusal", "swap", "fabrication", "malformed", "ambiguous", "error"]


def norm(s):
    return str(os.path.basename(str(s))).strip().lower().lstrip(".")


def is_filename(a):
    import re
    return bool(re.fullmatch(r"[\w.\-]+\.(py|md|json|txt|pyc|log|csv|exe|sh)", str(a).strip(), re.I))


def classify(ans, expect_str, corpus):
    exp = {norm(e) if e != "none" else "none" for e in expect_str.split("|")}
    a = str(ans).strip()
    if (norm(a) if a != "NONE" else "none") in exp:
        return "correct"
    if a == "NONE":
        return "refusal"
    if not is_filename(a):
        return "malformed"
    return "swap" if norm(a) in corpus else "fabrication"


def report(path, corpus, out=sys.stdout):
    rows = [json.loads(l) for l in open(path, encoding="utf-8")]
    p = lambda *a: print(*a, file=out)
    p(f"\n=== {os.path.basename(path)} ({len(rows)} rows) ===")

    sel = {(r["qid"], r["rep"]): r for r in rows if r["arm"] == "chunked2_select"}
    ver = {(r["qid"], r["rep"]): r for r in rows if r["arm"] == "chunked2_verify"}
    fin = {(r["qid"], r["rep"]): r for r in rows if r["arm"] == "chunked2"}

    p(f"\n-- two-pass arm, three aggregation rules ({len(fin)} question-repeats) --")
    tally = {k: collections.Counter() for k in ("strict", "lenient", "pass1")}
    ansb = {k: [0, 0] for k in tally}
    detail = []
    for key, f in sorted(fin.items()):
        s, v = sel.get(key), ver.get(key)
        pick = s["answer"] if s else "NONE"
        vans = v["answer"] if v else "(skipped)"
        picked_file = v["obj_file"] if v and v.get("obj_file") else ""
        strict = f["answer"]                                   # as run
        if not picked_file:
            lenient = pass1 = "NONE"
        else:
            pass1 = os.path.basename(picked_file)
            # veto only on a DIFFERENT named file; NONE from pass 2 is no information
            lenient = ("NONE" if (is_filename(vans) and norm(vans) != norm(picked_file))
                       else pass1)
        for name, a in (("strict", strict), ("lenient", lenient), ("pass1", pass1)):
            c = classify(a, f["expect"], corpus)
            tally[name][c] += 1
            if f["tok_present"]:
                ansb[name][1] += 1; ansb[name][0] += (c == "correct")
        detail.append((key[0], key[1], pick, vans, strict, lenient, pass1,
                       f["expect"], f["tok_present"]))
    for name in ("strict", "lenient", "pass1"):
        c = tally[name]
        p(f"  {name:8} " + " ".join(f"{x[:5]}={c[x]}" for x in CLS if c[x]) +
          f"   answerable {ansb[name][0]}/{ansb[name][1]}")

    p(f"\n  {'qid':14} {'rep':>3} {'pass1 select':22} {'pass2':20} "
      f"{'strict':16} {'lenient':16} expect")
    for q, r, pick, vans, st, le, p1, exp, tok in detail:
        p(f"  {q:14} {r:>3} {str(pick)[:22]:22} {str(vans)[:20]:20} "
          f"{st[:16]:16} {le[:16]:16} {exp}")

    sh = [r for r in rows if r["arm"] == "pair_shuffled"]
    if sh:
        p("\n-- pair_shuffled (de-confound for measurement 6's k=2) --")
        for sd in sorted({r["seed"] for r in sh}):
            s = [r for r in sh if r["seed"] == sd]
            a = [r for r in s if r["tok_present"]]
            c = collections.Counter(classify(r["answer"], r["expect"], corpus)
                                    if r["answer"] != "AMBIGUOUS" else "ambiguous" for r in s)
            ok = sum(1 for r in a if (r["answer"] != "AMBIGUOUS" and
                                      classify(r["answer"], r["expect"], corpus) == "correct"))
            p(f"  seed {sd}: answerable {ok}/{len(a)}   " +
              " ".join(f"{x[:5]}={c[x]}" for x in CLS if c[x]))
        a = [r for r in sh if r["tok_present"]]
        ok = sum(1 for r in a if (r["answer"] != "AMBIGUOUS" and
                                  classify(r["answer"], r["expect"], corpus) == "correct"))
        p(f"  pooled: answerable {ok}/{len(a)}")
    return rows


def corpus_files(rep):
    out = set()
    for _p, _d, fs in os.walk(rep):
        for f in fs:
            out.add(f.lower().lstrip("."))
    return out


if __name__ == "__main__":
    corpus = corpus_files(os.environ.get("FIT_CORPUS",
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "replica")))
    for a in sys.argv[1:]:
        report(a, corpus)
