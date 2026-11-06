"""
attenuate.py - dynamic attenuation: find the window a model can actually work in,
at run time, using checks that contain no model.

WHY THIS EXISTS (measured, 30-31 Oct 2026)

  granite4:3b verifies at separation +1.00 on a 1,200-char window and degrades to
  +0.75 at 3,600, where it invents a filename that is not in the corpus. gemma3:1b
  fails the other way: it still affirms every file it is shown, at every size.
  The failure is a function of PAYLOAD SIZE, not of elapsed time - within a model,
  its wrong answers are its FASTER ones.

  So the engine should not be told a window. It should start from the calibrated
  guess and shrink until a deterministic check passes, or refuse.

THE CONSTRAINT THAT MATTERS

  Every headline in this project that was killed by a later control was killed by
  a check with no model in it. The attenuation trigger is therefore never the
  model's own judgement. Two checks, both arithmetic:

    EXISTENCE  - is the named file in the corpus?  Catches FABRICATION.
    SPAN       - does the quoted evidence literally occur in the named file?
                 Catches SWAPS, which existence cannot: in measurement 8 all 16
                 routing errors named a real file, just the wrong one, so
                 existence checking would have caught exactly none of them.

  UNVALIDATED: the span check's false-rejection rate. A model that paraphrases
  instead of quoting fails a check it should pass. Measure before trusting.
"""
import json
import re

FLOOR = 300          # below this a window cannot hold useful evidence
NONE = "NONE"


# ---------------------------------------------------------------- contract ---
PROMPT = (
    "You are given ONE file. Decide whether it contains the answer to the question.\n"
    "Reply with JSON only, no prose, no code fence:\n"
    '  {{"file": "<filename>", "span": "<the exact text from the file that answers '
    'it, copied verbatim>"}}\n'
    'If the file does not contain the answer, reply exactly {{"file": "NONE", "span": ""}}.\n'
    "The span must be copied character for character from the file. Do not paraphrase.\n\n"
    "QUESTION: {q}\n\n## File: {fname}\n```\n{body}\n```\n"
)

# Variant B. Identical to PROMPT except for the span requirement. Measured 31 Oct:
# granite4:3b returned 5 FRAGMENTS of 16 ("print(f", "item[", four spaces) under
# PROMPT. That has two explanations - the model cannot quote, or it was never told
# what a span is - and they have different fixes. This variant separates them.
PROMPT_MINLEN = (
    "You are given ONE file. Decide whether it contains the answer to the question.\n"
    "Reply with JSON only, no prose, no code fence:\n"
    '  {{"file": "<filename>", "span": "<the exact text from the file that answers '
    'it, copied verbatim>"}}\n'
    'If the file does not contain the answer, reply exactly {{"file": "NONE", "span": ""}}.\n'
    "RULES FOR THE SPAN:\n"
    "  * Copy it character for character from the file. Do not paraphrase, do not\n"
    "    join two lines together, do not replace any word with a placeholder.\n"
    "  * It must be AT LEAST ONE COMPLETE LINE and at least 30 characters.\n"
    "  * A fragment such as `print(f` or `item[` is not acceptable.\n\n"
    "QUESTION: {q}\n\n## File: {fname}\n```\n{body}\n```\n"
)

# Variant C - the escaping-free contract. MEASURED 31 Oct: all five of
# granite4:3b's fragment spans stop at exactly the character that would need
# escaping inside a JSON string ("print(f" and "item[" are each followed in the
# source by a double quote). The model is not failing to READ; it is failing to
# EMIT a quote inside a JSON string under schema-constrained decoding. So stop
# asking for text. Ask for LINE NUMBERS - integers need no escaping - and let
# the engine read those lines itself and check them. The verification is the
# same strength and the encoding problem disappears.
PROMPT_LINES = (
    "You are given ONE file, with every line numbered.\n"
    "Decide whether it contains the answer to the question.\n"
    "Reply with JSON only, no prose, no code fence:\n"
    '  {{"file": "<filename>", "first_line": <int>, "last_line": <int>}}\n'
    'If the file does not contain the answer, reply exactly '
    '{{"file": "NONE", "first_line": 0, "last_line": 0}}.\n'
    "Give the smallest line range that contains the answer. Numbers only - do\n"
    "not quote the text.\n\n"
    "QUESTION: {q}\n\n## File: {fname}\n```\n{body}\n```\n"
)

SCHEMA_LINES = {"type": "object",
                "properties": {"file": {"type": "string"},
                               "first_line": {"type": "integer"},
                               "last_line": {"type": "integer"}},
                "required": ["file", "first_line", "last_line"]}

SCHEMA = {"type": "object",
          "properties": {"file": {"type": "string"}, "span": {"type": "string"}},
          "required": ["file", "span"]}


def window_text(text, window, offset=None):
    """Cut `window` chars CENTRED on offset.

    Caught by this module's own self-test, 31 Oct: a window that truncates from
    the start deletes the evidence as it shrinks, so attenuation would convert a
    correct answer into an honest-looking NONE and destroy recall while appearing
    to work. The candidate offset comes from the deterministic ranker, which knows
    where the matched token sits; with no offset the prefix is the only option and
    attenuation is unsafe, so the caller is told.
    """
    if window >= len(text):
        return text, 0
    if offset is None:
        return text[:window], 0
    start = max(0, min(int(offset) - window // 2, len(text) - window))
    return text[start:start + window], start


def build_prompt(question, fname, text, window, offset=None, variant="strict"):
    body, start = window_text(text, window, offset)
    if variant == "lines":
        base = text[:start].count("\n") + 1
        body = "\n".join(f"{base + i:>5} | {ln}"
                          for i, ln in enumerate(body.splitlines()))
        return PROMPT_LINES.format(q=question, fname=fname, body=body)
    tpl = PROMPT_MINLEN if variant == "minlen" else PROMPT
    return tpl.format(q=question, fname=fname, body=body)


def parse_lines(raw):
    """-> (file, first_line, last_line). Integers need no escaping."""
    if raw is None:
        return None, 0, 0
    t = re.sub(r"^```(?:json)?|```$", "", str(raw).strip(), flags=re.M).strip()
    m = re.search(r"\{.*\}", t, re.S)
    if not m:
        return None, 0, 0
    try:
        d = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None, 0, 0
    try:
        return (str(d.get("file", "")).strip() or None,
                int(d.get("first_line", 0)), int(d.get("last_line", 0)))
    except (TypeError, ValueError):
        return str(d.get("file", "")).strip() or None, 0, 0


def check_lines(fname, lo, hi, corpus, evidence=None, max_span=40):
    """The engine reads the cited lines itself. No text crosses the boundary."""
    if fname is None:
        return False, "unparseable"
    if fname.upper() == NONE:
        return True, "refusal"
    keys = {k.lower().lstrip("."): k for k in corpus}
    key = keys.get(fname.lower().lstrip("."))
    if key is None:
        return False, "names a file outside the index"
    lines = corpus[key].splitlines()
    if not (1 <= lo <= len(lines)) or not (lo <= hi <= len(lines)):
        return False, f"line range {lo}-{hi} outside 1-{len(lines)}"
    if hi - lo + 1 > max_span:
        return False, f"range of {hi - lo + 1} lines is not a citation"
    if evidence and evidence not in "\n".join(lines[lo - 1:hi]):
        return False, "cited lines do not contain the evidence"
    return True, f"lines {lo}-{hi} verified"


def parse(raw):
    """Model output -> (file, span). Tolerant of fences; never guesses a filename."""
    if raw is None:
        return None, None
    s = str(raw).strip()
    s = re.sub(r"^```(?:json)?|```$", "", s, flags=re.M).strip()
    m = re.search(r"\{.*\}", s, re.S)
    if m:
        try:
            d = json.loads(m.group(0))
            return (str(d.get("file", "")).strip() or None,
                    str(d.get("span", "")))
        except json.JSONDecodeError:
            pass
    if s.upper().startswith(NONE):
        return NONE, ""
    return None, None                      # unparseable is not an answer


# ------------------------------------------------------------------ checks ---
def _norm(s):
    """Collapse whitespace. Nothing else - no casefolding, no punctuation games."""
    return re.sub(r"\s+", " ", str(s)).strip()


_ESCAPES = (("\n", "\\n"), ("\t", "\\t"), ("\r", "\\r"))


def _span_forms(span):
    """Both readings of an escape sequence, because JSON decodes what source stores.

    Measured 31 Oct: gemma4:31b quoted `print(f"\\n[Error] ...")` from a .py file
    correctly, but its JSON span decoded \\n to a real newline while the file holds
    the two characters backslash-n. That is 1 of 16 hits - a 6% false-rejection
    rate created entirely by escaping, not by the model. Trying both readings is
    arithmetic, not judgement, so it costs the check nothing.
    """
    forms = {str(span)}
    lit = str(span)
    for real, source in _ESCAPES:
        lit = lit.replace(real, source)
    forms.add(lit)
    return {_norm(f) for f in forms if _norm(f)}


def check_existence(fname, corpus):
    if fname is None:
        return False, "unparseable"
    if fname.upper() == NONE:
        return True, "refusal"
    keys = {k.lower().lstrip("."): k for k in corpus}
    if fname.lower().lstrip(".") in keys:
        return True, "exists"
    return False, f"fabrication: {fname!r} is not in the corpus"


def check_span(fname, span, corpus, min_len=8):
    if fname is None:
        return False, "unparseable"
    if fname.upper() == NONE:
        return True, "refusal"
    keys = {k.lower().lstrip("."): k for k in corpus}
    key = keys.get(fname.lower().lstrip("."))
    if key is None:
        return False, "fabrication"
    if len(_norm(span)) < min_len:
        return False, "span too short to verify"
    hay = _norm(corpus[key])
    for form in _span_forms(span):
        if form in hay:
            return True, "span verified"
    return False, "span not found in the named file"


def deterministic_check(fname, span, corpus, use_span=True):
    ok, why = check_existence(fname, corpus)
    if not ok:
        return False, why
    if not use_span:
        return True, why
    return check_span(fname, span, corpus)



# --------------------------------------------- the bare one-field contract ---
# Lifted verbatim from calibrate.py so the arms are comparable. NOTE what this
# is and is not: it is NOT schema-free. It constrains the reply to
# {"answer": "<filename>"} - ONE field. The span and lines contracts add a
# SECOND field the model must fill. That is the only difference between them,
# so it is the difference the refusal measurements are attributable to.
RULES_BARE = ('Answer using ONLY the context above. If the context does not contain the evidence,\n'
              'the answer is NONE -- that is a valid and often correct answer, not a failure.\n'
              'Reply with JSON only: {"answer": "<filename>"} or {"answer": "NONE"}')

SCHEMA_BARE = {"type": "object",
               "properties": {"answer": {"type": "string"}},
               "required": ["answer"]}


def build_prompt_bare(question, fname, text, window, offset=None):
    body, _ = window_text(text, window, offset)
    return (f"--- BEGIN CONTEXT ---\n"
            f"## Bound Source\n\n* **File**: `{fname}`\n```\n{body}\n```\n"
            f"--- END CONTEXT ---\n\nQuestion: {question}\n\n{RULES_BARE}\n")


def parse_bare(raw):
    """-> filename or NONE. One field, so nothing can truncate mid-citation."""
    if raw is None:
        return None
    t = re.sub(r"^```(?:json)?|```$", "", str(raw).strip(), flags=re.M).strip()
    try:
        return (json.loads(t).get("answer") or "").strip() or None
    except Exception:
        m = re.search(r'"answer"\s*:\s*"([^"]*)"', t)
        return (m.group(1).strip() if m else None) or None


# ------------------------------------------------------------- attenuation ---
def attenuate(ask, question, fname, text, corpus, window, offset=None,
              floor=FLOOR, use_span=True, max_steps=4, variant="strict"):
    """ask(prompt) -> raw string. Halve the window until a check passes, or refuse.

    Returns a receipt. The caller is never handed a bare answer: every field the
    engine acted on is in the record, including the windows that failed.
    """
    trail = []
    w = int(window)
    for _ in range(max_steps):
        raw = ask(build_prompt(question, fname, text, w, offset, variant))
        # D8 (found 31 Oct): this loop called parse()/check_span() whatever the
        # variant, so the lines contract - which returns {file, first_line,
        # last_line} and no text span - failed every check and attenuated to
        # NONE on all 16 questions. That 0/16 was a wiring defect, not a result.
        if variant == "lines":
            f, lo, hi = parse_lines(raw)
            sp = f"{lo}-{hi}" if lo or hi else ""
            ok, why = (check_lines(f, lo, hi, corpus) if use_span
                       else check_existence(f, corpus))
        else:
            f, sp = parse(raw)
            ok, why = deterministic_check(f, sp, corpus, use_span=use_span)
        refused = (f or "").upper() == NONE
        trail.append(dict(window=w, offset=offset, file=f,
                          span=(sp or "")[:80], ok=ok, why=why, refused=refused))

        # A REFUSAL IS NOT EVIDENCE OF ABSENCE. This is harness error H5, which
        # the project already made once: a two-pass gate took a small model's
        # NONE as proof the evidence was missing, routing every answer through
        # the operation that model was worst at. The measurements say a NONE at
        # a WIDE window is the least trustworthy kind - granite4:3b's hit rate
        # is 0.94 at 3,600 chars against 1.00 at 1,200, so it misses at width
        # what it finds when narrowed. So a refusal is recorded and the loop
        # keeps narrowing; NONE is only returned when no window produced a
        # verified answer.
        if ok and not refused:
            return dict(answer=f, span=sp, window=w, verified=True,
                        attenuated=len(trail) - 1, trail=trail)
        if w // 2 < floor:
            break
        w //= 2
    refusals = sum(1 for t in trail if t.get("refused"))
    return dict(answer=NONE, span="", window=w, verified=False,
                attenuated=len(trail) - 1, trail=trail, refusals=refusals,
                reason=("the model refused at every window tried" if refusals == len(trail)
                        else "no window passed a deterministic check"))


# ------------------------------------------- self-test: negatives are the point
def selftest():
    corpus = {"local_runner.py": "import os\nAPI_URL = 'https://x.test/v1/run'\n",
              "notes.md": "# notes\nThe daemon polls every 30 seconds.\n",
              ".error_ledger.json": '{"errors": []}'}
    f = []
    def ck(name, got, want):
        if got != want:
            f.append(f"{name}: got {got!r} want {want!r}")

    # parse
    ck("parse-json", parse('{"file":"notes.md","span":"polls every 30"}'),
       ("notes.md", "polls every 30"))
    ck("parse-fenced", parse('```json\n{"file":"notes.md","span":"x"}\n```')[0], "notes.md")
    ck("parse-garbage", parse("I think it is probably notes.md"), (None, None))

    # existence
    ck("exists", check_existence("notes.md", corpus)[0], True)
    ck("exists-dotfile", check_existence("error_ledger.json", corpus)[0], True)
    ck("fabrication", check_existence("memory_inject.md", corpus)[0], False)
    ck("none-is-honest", check_existence(NONE, corpus)[0], True)

    # span - the check existence cannot do
    ck("span-ok", check_span("notes.md", "polls every 30 seconds", corpus)[0], True)
    ck("span-whitespace", check_span("notes.md", "polls   every\n30 seconds", corpus)[0], True)
    ck("SWAP-caught", check_span("local_runner.py", "polls every 30 seconds", corpus)[0], False)
    ck("span-paraphrase-rejected",
       check_span("notes.md", "it checks twice a minute", corpus)[0], False)
    ck("span-too-short", check_span("notes.md", "the", corpus)[0], False)

    # the loop: a model that fabricates at a wide window and recovers at a narrow one
    doc = "x " * 1200 + "The daemon polls every 30 seconds." + " y" * 1200
    off = doc.index("The daemon polls")

    def flaky(prompt):
        # fabricates while the body is wide, answers correctly once it narrows
        body = prompt.split("```")[1]
        return ('{"file":"memory_inject.md","span":"invented"}' if len(body) > 1500
                else '{"file":"notes.md","span":"polls every 30 seconds"}')
    r = attenuate(flaky, "how often does it poll?", "notes.md", doc, corpus,
                  window=3600, offset=off)
    ck("loop-recovers", (r["verified"], r["answer"]), (True, "notes.md"))
    ck("loop-attenuated", r["attenuated"] > 0, True)

    # escaping control: source stores backslash-n, JSON decodes a newline
    esc = {"local_runner.py": 'print(f"\\n[Error] Failed to connect")'}
    ck("escaped-span-accepted",
       check_span("local_runner.py", 'print(f"\n[Error] Failed to connect")', esc)[0], True)
    ck("wrong-span-still-rejected",
       check_span("local_runner.py", 'print(f"\n[Error] totally different")', esc)[0], False)

    # centring control: the evidence must survive shrinking
    long_doc = "x " * 1200 + "The daemon polls every 30 seconds." + " y" * 1200
    o = long_doc.index("The daemon polls")
    ck("centred-window-keeps-evidence",
       "polls every 30 seconds" in window_text(long_doc, 400, o)[0], True)
    ck("prefix-window-loses-it",
       "polls every 30 seconds" in window_text(long_doc, 400, None)[0], False)

    # H5 control: a refusal at a wide window must not end the search
    doc2 = "z " * 1200 + "The daemon polls every 30 seconds." + " w" * 1200
    o2 = doc2.index("The daemon polls")

    def refuses_wide(prompt):
        body = prompt.split("```")[1]
        return ('{"file":"NONE","span":""}' if len(body) > 1500
                else '{"file":"notes.md","span":"polls every 30 seconds"}')
    r3 = attenuate(refuses_wide, "q", "notes.md", doc2, corpus, window=3600, offset=o2)
    ck("refusal-does-not-end-search", (r3["verified"], r3["answer"]), (True, "notes.md"))

    # but a model that refuses at EVERY window is believed, and says why
    r4 = attenuate(lambda p: '{"file":"NONE","span":""}', "q", "notes.md",
                   doc2, corpus, window=3600, offset=o2)
    ck("refusal-everywhere-is-honest", (r4["verified"], r4["answer"]), (False, NONE))
    ck("refusal-reason", "refused at every window" in r4["reason"], True)

    # a model that is wrong at every window must REFUSE, not be believed
    r2 = attenuate(lambda p: '{"file":"memory_inject.md","span":"invented"}',
                   "q", "notes.md", "text", corpus, window=3600)
    ck("loop-refuses", (r2["verified"], r2["answer"]), (False, NONE))
    return f
