"""
heldout.py - generate a fresh probe question set from the corpus, deterministically.

WHY THIS EXISTS. Eleven hand-written questions have carried seven measurements.
Anything fitted on them and scored on them is fitted on its own test set, and
"write a held-out set by hand" just moves the problem: I would pick questions I
expect to work. So the set is GENERATED, from a seed, and a different seed gives
a different set. Overfitting is prevented by construction rather than by
intention.

WHAT A GOOD GENERATED QUESTION NEEDS, all checkable without a model:
  * the evidence token occurs EXACTLY ONCE in the whole corpus, so ground truth
    is a single file and not a judgement call;
  * it sits past `min_offset` bytes into its file, so head-of-file snippets do
    not answer it for free (the confound found in the v6 question set);
  * it is long enough not to be noise.

QUESTION STYLE. The token is MASKED in the question and its surrounding line is
quoted, so the question cannot be answered by string-matching the token itself.
The surrounding context still leaks lexically - which is fine and is the point:
`baseline_index.py` measures exactly how much, and every model score on a
generated set is reported as a DELTA over that deterministic baseline. A set is
not required to be hard; it is required to have a known floor.

usage:  python heldout.py 20 7        (20 questions, seed 7)
"""
import os, re, sys, json, random, collections

PROBE_ROOT = os.environ.get("FIT_PROBE_ROOT",
                            os.path.dirname(os.path.abspath(__file__)))
PKG = os.path.dirname(os.path.abspath(__file__))
RECORDS = os.environ.get("FIT_RECORDS", os.path.join(os.path.dirname(PKG), "records"))
RESULTS = os.environ.get("FIT_RESULTS", os.path.join(os.path.dirname(PKG), "results"))
CORPUS = os.environ.get("FIT_CORPUS") or next(
    (q for q in (os.path.join(os.path.dirname(PKG), "replica"),
                 os.path.join(os.path.dirname(PKG), "corpus_fixture")) if os.path.isdir(q)),
    os.path.join(os.path.dirname(PKG), "corpus_fixture"))
REPLICA = CORPUS
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{5,}|\b\d{4,}\b")
# tokens that are structural rather than evidential - matching them tests nothing
BORING = set(("import", "return", "self", "python", "encoding", "default", "object",
              "string", "number", "format", "result", "values", "source", "target",
              "content", "context", "payload", "workspace", "engine")) 


def read_corpus(root=REPLICA):
    out = {}
    for par, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "staging", ".claude")]
        for f in files:
            if f.endswith(".pyc"):
                continue
            p = os.path.join(par, f)
            try:
                out[f] = open(p, encoding="utf-8").read()
            except Exception:
                pass
    return out


def generate(n=20, seed=0, min_offset=800, corpus=None):
    corpus = corpus or read_corpus()
    where = collections.defaultdict(set)          # token -> {files}
    first = {}                                    # (file, token) -> offset
    for fname, text in corpus.items():
        for m in TOKEN_RE.finditer(text):
            t = m.group(0)
            if t.lower() in BORING:
                continue
            where[t].add(fname)
            first.setdefault((fname, t), m.start())

    names = set(corpus)                           # every filename in the corpus
    cands = []
    for t, files in where.items():
        if len(files) != 1:                       # unique by tokenisation...
            continue
        fname = next(iter(files))
        # ...and unique by SUBSTRING too. The model matches substrings, not tokens,
        # so a token that is unique as a token but appears inside a longer word
        # elsewhere does not have a single defensible home.
        if sum(txt.count(t) for txt in corpus.values()) != 1:
            continue
        off = first[(fname, t)]
        if off < min_offset:
            continue
        text = corpus[fname]
        ls = text.rfind("\n", 0, off) + 1
        le = text.find("\n", off)
        line = text[ls:le if le != -1 else len(text)].strip()
        if len(line) < 12 or len(line) > 160:
            continue
        masked = line.replace(t, "____")
        # The quoted line must not NAME a file. A line mentioning `local_runner.py`
        # inside notes.md either hands over the answer or points at the wrong file;
        # either way the question stops measuring binding.
        stems = {nm.lower() for nm in names} | {nm.split(".")[0].lower() for nm in names}
        low = masked.lower()
        if any(st in low for st in stems if len(st) > 3):
            continue
        if re.search(r"[\w\-]+\.(py|md|json|txt|log|csv)\b", masked, re.I):
            continue
        # The line must carry enough content to be answerable at all. "5. **____:**"
        # is not a question, it is noise with a blank in it.
        body = [w for w in re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}", masked)]
        if len(body) < 4:
            continue
        cands.append(dict(tok=t, home=[fname], offset=off, line=line, masked=masked))

    cands.sort(key=lambda c: (c["home"][0], c["offset"], c["tok"]))   # stable
    random.Random(seed).shuffle(cands)
    picked, used_files = [], collections.Counter()
    for c in cands:                               # spread across files
        if used_files[c["home"][0]] >= max(2, n // max(len(corpus), 1) + 2):
            continue
        used_files[c["home"][0]] += 1
        picked.append(c)
        if len(picked) >= n:
            break

    qs = []
    for i, c in enumerate(picked):
        qs.append(dict(
            id=f"g{seed}_{i:02d}",
            tok=c["tok"], home=c["home"], offset=c["offset"],
            q=("Which file contains a line reading `" + c["masked"] +
               "` , where ____ is a single identifier?")))
    return qs


def summarise(qs, corpus=None):
    corpus = corpus or read_corpus()
    by = collections.Counter(q["home"][0] for q in qs)
    print(f"generated {len(qs)} questions over {len(by)} files: {dict(by)}")
    print(f"min offset {min(q['offset'] for q in qs)}, "
          f"median {sorted(q['offset'] for q in qs)[len(qs)//2]}, "
          f"max {max(q['offset'] for q in qs)}")
    leak = sum(1 for q in qs if q["tok"] in q["q"])
    print(f"questions whose own evidence token appears in the question text: {leak} "
          f"(must be 0 - the token is masked)")
    uniq = all(sum(t.count(q['tok']) for t in corpus.values()) == 1 for q in qs)
    print(f"every evidence token unique across the corpus: {uniq}")


if __name__ == "__main__":
    if os.path.exists(os.path.join(CORPUS, "REDACTION.md")):
        raise SystemExit(
            "heldout.py generates questions from source text and cannot use the\n"
            "redacted fixture - the questions would be meaningless. The question\n"
            "set used for every published run ships frozen at\n"
            "records/questions_seed0_n20.json. Set FIT_CORPUS to a real tree.")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    qs = generate(n, seed)
    summarise(qs)
    out = os.path.join(PROBE_ROOT, f"heldout_seed{seed}_n{len(qs)}.json")
    json.dump(qs, open(out, "w", encoding="utf-8"), indent=1)
    print("wrote", out)
    for q in qs[:5]:
        print(f"  {q['id']} -> {q['home'][0]} @{q['offset']}\n     {q['q'][:120]}")
