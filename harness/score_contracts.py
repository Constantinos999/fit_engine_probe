"""score_contracts.py - build the contract x model matrix from raw run records.

Reads every attenuate_*.jsonl in this folder, re-scores each row with the
deterministic check the ENGINE would apply (including the evidence clause that
D9 silently disabled), and writes contract_matrix.json + contract_matrix.md.

Model-free: it makes no network calls and can be run any time, offline.
Re-scoring from raw rows rather than trusting a run's own summary is the point -
the first lines run reported hit 16/16 / fa 16/16 and the truth was 15/16 / 0/16.

usage:  python score_contracts.py
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
sys.path.insert(0, HERE)
import attenuate as at
import heldout as ho


def variant_of(path):
    m = re.match(r"attenuate_(.+?)(?:_(minlen|lines))?\.jsonl$", os.path.basename(path))
    if not m:
        return None, None
    return m.group(1), (m.group(2) or "strict")


def score(path, corpus, qmap):
    model, variant = variant_of(path)
    if model is None:
        return None
    rows = [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]
    out = {"model": model, "variant": variant, "file": os.path.basename(path),
           "n_rows": len(rows)}
    for arm in ("hit", "fa"):
        allsub = [r for r in rows if r.get("arm") == arm]
        # ERRORED CALLS ARE NOT RESULTS. An HTTP 404 or a timeout is the harness
        # failing, not the model answering wrongly - counting it in the
        # denominator reports a dead run as a perfect-zero score. This is the
        # same defect calibrate.py was fixed for on 30 Oct (a single HTTP 502
        # turned gpt-oss:20b's +1.00 into +0.94); it was reintroduced here on
        # 31 Oct and caught when gemma4:31b and gpt-oss:20b both scored 0/16
        # with 32 of 48 calls erroring. Rates are computed over calls that
        # actually returned; the error count is reported alongside.
        errors = sum(1 for r in allsub if r.get("error"))
        sub = [r for r in allsub if not r.get("error")]
        named_right = verified = refused = 0
        for r in sub:
            q = qmap.get(r.get("qid"))
            f = r.get("file")
            if (f or "").upper() == "NONE":
                refused += 1
            home = (q or {}).get("home", [""])
            home = home[0] if isinstance(home, list) else str(home)
            if (f or "").lower().lstrip(".") == home.lower().lstrip("."):
                named_right += 1
            tok = (q or {}).get("tok")
            sp = r.get("span") or ""
            if variant == "lines":
                try:
                    lo, hi = [int(x) for x in sp.split("-")[:2]]
                except Exception:
                    lo = hi = 0
                ok, _ = at.check_lines(f, lo, hi, corpus, evidence=tok)
            else:
                ok, _ = at.check_span(f, sp, corpus)
                # a span contract only cites honestly if the quoted text is
                # really in the file AND really carries the evidence
                if ok and tok and tok not in (sp or ""):
                    ok = tok in (sp or "")
            if ok and (f or "").upper() != "NONE":
                verified += 1
        n = max(len(sub), 1)
        out[arm] = {"n": len(sub), "n_attempted": len(allsub),
                    "named_right": named_right,
                    "citation_verified": verified, "refused": refused,
                    "errors": errors, "rate": round(verified / n, 3)}
    # what the ENGINE would actually emit: an answer only when the citation
    # verifies. A swap that cannot produce a verifiable citation is refused
    # by the harness, whether or not the model had the grace to refuse itself.
    att = out["hit"]["n_attempted"] + out["fa"]["n_attempted"]
    err = out["hit"]["errors"] + out["fa"]["errors"]
    out["errors"] = err
    out["void"] = err > 0 and err >= att / 2
    out["effective_false_affirm"] = out["fa"]["rate"]
    out["separation"] = round(out["hit"]["rate"] - out["fa"]["rate"], 3)
    return out


QUESTIONS = os.environ.get("FIT_QUESTIONS",
                           os.path.join(RECORDS, "questions_seed0_n20.json"))


def load_questions(corpus):
    """Prefer the frozen manifest; regenerate only if it is absent.

    Regenerating needs the full corpus. If neither is available the matrix
    would score every row 0/16 while exiting 0 - a silent wrong answer of
    exactly the kind this paper is about - so that case raises instead.
    """
    if os.path.exists(QUESTIONS):
        qs = json.load(open(QUESTIONS, encoding="utf-8"))
        return {q["id"]: q for q in qs}
    if not corpus:
        raise SystemExit(
            "no question manifest at %s and no corpus at %s - cannot score. "
            "Set FIT_QUESTIONS or FIT_CORPUS." % (QUESTIONS, CORPUS))
    return {q["id"]: q for q in ho.generate(20, 0, corpus=corpus)}


def main():
    corpus = ho.read_corpus()
    if not corpus:
        raise SystemExit("corpus at %s is empty - every citation check would "
                         "fail and the matrix would read 0/16. Set FIT_CORPUS."
                         % CORPUS)
    qmap = load_questions(corpus)
    results = []
    for p in sorted(glob.glob(os.path.join(RECORDS, "attenuate_*.jsonl"))):
        if ".bak." in p:
            continue
        s = score(p, corpus, qmap)
        if s:
            results.append(s)
    results.sort(key=lambda s: (-s["separation"], s["model"]))

    hdr = (f"| model | contract | citation verified | false affirm | separation | errored |\n"
           f"|---|---|---|---|---|---|\n")
    body = "".join(
        f"| `{s['model']}` | {s['variant']}{' **VOID**' if s.get('void') else ''} | "
        f"{s['hit']['citation_verified']}/{s['hit']['n']} | "
        f"{s['fa']['citation_verified']}/{s['fa']['n']} | "
        f"{s['separation']:+.3f} | {s.get('errors',0)} |\n" for s in results)
    md = (f"# Contract x model matrix\n\n"
          f"Re-scored from raw rows {time.strftime('%Y-%m-%d %H:%M')}. "
          f"`citation verified` counts rows whose citation passes the engine's own\n"
          f"deterministic check, evidence clause included. `false affirm` is the same\n"
          f"check on the wrong-file arm: a model may name a wrong file freely, it is\n"
          f"counted against it only if a bogus citation would have been BELIEVED.\n\n"
          + hdr + body)
    json.dump(results, open(os.path.join(RESULTS, "contract_matrix.json"), "w",
                            encoding="utf-8"), indent=2)
    open(os.path.join(RESULTS, "contract_matrix.md"), "w", encoding="utf-8").write(md)
    print(md)
    print(f"[ok] wrote contract_matrix.json and contract_matrix.md "
          f"({len(results)} runs scored)")


if __name__ == "__main__":
    main()
