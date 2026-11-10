"""paper_trail.py - emit hand-checkable traces of real cases.

DeepSeek's prescription, item 4 on the blueprint and the grey GATE box: trace
20-30 REAL cases by hand before trusting any database built over them. The
predecessor skipped it for automated probes and said so in the session log; D9
is what that cost - an evidence check sat disabled by a key-name typo, invisible
to every probe, because the probes asked the scorer and the scorer was wrong.

Every case below prints four things, so a reader can check it WITHOUT running
anything: the question, what the model answered, what the engine's deterministic
check said, and WHERE THE EVIDENCE ACTUALLY IS on disk, quoted with its line
number. If the check and the disk disagree, the case is wrong and visible.

Model-free. Reads only saved raw rows and the corpus.
usage:  python paper_trail.py          -> PAPER_TRAIL.md
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


def locate(tok, corpus):
    """Where does this token REALLY live? -> list of (file, lineno, text)."""
    out = []
    for f, text in corpus.items():
        for i, ln in enumerate(text.splitlines(), 1):
            if tok and tok in ln:
                out.append((f, i, ln.strip()))
    return out


def rows_from(path):
    return [json.loads(l) for l in open(path, encoding="utf-8") if l.strip()]


def trace(r, q, corpus, contract):
    """One case, fully resolved against disk."""
    tok = q.get("tok")
    home = q["home"][0] if isinstance(q.get("home"), list) else str(q.get("home"))
    said_file = r.get("file")
    span = r.get("span") or ""
    truth = locate(tok, corpus)

    if contract == "lines":
        try:
            lo, hi = [int(x) for x in span.split("-")[:2]]
        except Exception:
            lo = hi = 0
        ok, why = at.check_lines(said_file, lo, hi, corpus, evidence=tok)
        cited = ""
        key = {k.lower().lstrip("."): k for k in corpus}.get(
            (said_file or "").lower().lstrip("."))
        if key and lo >= 1:
            lines = corpus[key].splitlines()
            cited = " / ".join(x.strip() for x in lines[lo - 1:hi][:3])
    else:
        ok, why = at.check_span(said_file, span, corpus)
        cited = span

    right_file = (said_file or "").lower().lstrip(".") == home.lower().lstrip(".")
    if (said_file or "").upper() == "NONE":
        verdict = "REFUSAL"
    elif r.get("arm") == "fa":
        verdict = "SWAP CAUGHT" if not ok else "SWAP BELIEVED  <-- a false affirmation"
    elif right_file and ok:
        verdict = "CORRECT, citation verified"
    elif right_file and not ok:
        verdict = "RIGHT FILE, BAD CITATION  <-- caught only by the span check"
    else:
        verdict = "SWAP"

    return dict(qid=r.get("qid"), contract=contract, arm=r.get("arm"),
                question=q["q"], home=home, token=tok, shown=r.get("shown"),
                said_file=said_file, span=span, cited=cited,
                check_ok=ok, check_why=why, verdict=verdict,
                truth=truth[:3], secs=r.get("secs"))


def _public_blob(records_dir, questions):
    """Everything a reader of the release can already read: the raw per-call
    records, plus each question line with its blanked identifier restored.

    corpus_fixture/REDACTION.md promises nothing outside this set is disclosed.
    The trail has to honour the same promise or the two artifacts disagree."""
    blob = []
    try:
        for f in os.listdir(records_dir):
            if f.endswith((".json", ".jsonl")):
                blob.append(open(os.path.join(records_dir, f), encoding="utf-8",
                                 errors="ignore").read())
    except Exception:
        pass
    for q in (questions or []):
        if "____" in q.get("q", "") and q.get("tok"):
            blob.append(q["q"].replace("____", q["tok"]))
    return "\n".join(blob)


def _norm(s):
    s = s.replace("\\\\", "\\").replace("\\n", "\n").replace('\\"', '"')
    return re.sub(r"\s+", " ", s).strip()


def redact_private(text, blob, blob_norm):
    """Dot any fragment not already public, exactly as the fixture dots."""
    out = []
    for part in (text or "").split(" / "):
        s = part.strip()
        if not s:
            out.append(part); continue
        n = _norm(part)
        if s in blob or (len(n) >= 12 and n in blob_norm):
            out.append(part)
        else:
            out.append("".join(c if c == " " else "." for c in part))
    return " / ".join(out)


def main():
    if os.path.exists(os.path.join(CORPUS, "REDACTION.md")):
        raise SystemExit(
            "paper_trail.py quotes evidence text and regenerates the question\n"
            "set, so it cannot run against the redacted fixture at %s - it\n"
            "would emit dots and a different set of cases. The shipped\n"
            "measurements/PAPER_TRAIL.md was built from the real corpus.\n"
            "Point FIT_CORPUS at a real directory tree to rebuild it." % CORPUS)
    corpus = ho.read_corpus()
    qmap = {q["id"]: q for q in ho.generate(20, 0, corpus=corpus)}
    sources = [("attenuate_granite4-3b_lines.jsonl", "lines"),
               ("attenuate_granite4-3b.jsonl", "strict")]

    global _PUB, _PUBN
    _PUB = _public_blob(RECORDS, list(qmap.values()))
    _PUBN = _norm(_PUB)
    cases, seen = [], set()
    # deliberately spread across the failure taxonomy rather than taking the
    # first N - a paper trail of twenty correct answers teaches nothing
    want = ["RIGHT FILE, BAD CITATION", "SWAP BELIEVED", "SWAP CAUGHT",
            "REFUSAL", "CORRECT, citation verified", "SWAP"]
    pools = {w: [] for w in want}
    for fn, contract in sources:
        p = os.path.join(RECORDS, fn)
        if not os.path.exists(p):
            continue
        for r in rows_from(p):
            if r.get("arm") not in ("hit", "fa"):
                continue
            q = qmap.get(r.get("qid"))
            if not q:
                continue
            t = trace(r, q, corpus, contract)
            for w in want:
                if t["verdict"].startswith(w):
                    pools[w].append(t)
                    break

    # take up to 4 of each class, newest contract first, cap at 24
    for w in want:
        for t in pools[w][:4]:
            k = (t["qid"], t["contract"], t["arm"])
            if k in seen:
                continue
            seen.add(k)
            cases.append(t)
    cases = cases[:24]

    out = [f"# Paper trail - {len(cases)} real cases, traced by hand\n",
           f"Generated {time.strftime('%Y-%m-%d %H:%M')} by `paper_trail.py` from saved",
           "raw rows. No model was called. Every case can be checked against the",
           "repository without running anything: the question, the model's answer, the",
           "engine's deterministic verdict, and the evidence's true location on disk.\n",
           "This is item 4 on the blueprint (the grey GATE box) and DeepSeek's",
           "prescription: trace real cases before trusting a database built over them.",
           "It was skipped once, and D9 - an evidence check disabled by a key-name",
           "mismatch, invisible to every automated probe - is what that cost.\n",
           "---\n"]
    for i, t in enumerate(cases, 1):
        out.append(f"## Case {i} - {t['verdict']}\n")
        out.append(f"- **question** ({t['qid']}, {t['contract']} contract, "
                   f"`{t['arm']}` arm): {t['question']}")
        out.append(f"- **evidence token**: `{t['token']}`")
        out.append(f"- **file shown to the model**: `{t['shown']}`  ·  "
                   f"**home file**: `{t['home']}`")
        out.append(f"- **model answered**: `{t['said_file']}`  span `{t['span']}`")
        t["cited"] = redact_private(t["cited"], _PUB, _PUBN)
        if t["cited"]:
            out.append(f"- **what those lines actually say**: `{t['cited'][:160]}`")
        out.append(f"- **engine check**: {'PASS' if t['check_ok'] else 'FAIL'} "
                   f"- {t['check_why']}")
        if t["truth"]:
            tr = "; ".join(f"`{f}`:{n} -> `{x[:70]}`" for f, n, x in t["truth"])
            out.append(f"- **the token really lives at**: {tr}")
        else:
            out.append("- **the token really lives at**: nowhere in the corpus "
                       "(this is a false-affirm probe)")
        out.append("")
    md = "\n".join(out)
    open(os.path.join(MEASUREMENTS, "PAPER_TRAIL.md"), "w", encoding="utf-8").write(md)
    counts = {}
    for t in cases:
        counts[t["verdict"]] = counts.get(t["verdict"], 0) + 1
    print(f"[ok] PAPER_TRAIL.md - {len(cases)} cases")
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print(f"   {v:>2}  {k}")


if __name__ == "__main__":
    main()
