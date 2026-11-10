# Misbinding, not fabrication — attribution error in an offline developer agent

Supporting code and data for the Kaggle **Google — Gemma 4 Developer Agent, Paper
Track** submission by **Constantinos Eleftheriou**.

The paper reports one finding. When a small local model is asked which file in a
codebase contains a given fact, its wrong answers are almost never invented. They
are real files bound to the wrong source — the signature of an *illusory
conjunction*, not of fabrication. Across 1,754 classified outputs from five
models, genuine fabrication was zero. A citation contract asking for line numbers
instead of quoted text drives false attribution to 0 of 16 on every model tested,
from 1B to 3B, across three vendors.

Everything needed to re-derive the paper's central table is in this repository,
and it runs offline on a CPU in under a second.

---

## Reproduce the headline result

No model, no network, no GPU. Python 3.9+ and the standard library only.

```
cd harness
python score_contracts.py
```

This re-scores all 34 raw run records from scratch and writes
`results/contract_matrix.json` and `results/contract_matrix.md`. Expected output:

| model | contract | citation verified | false affirm | separation |
|---|---|---|---|---|
| `qwen2.5-coder-3b` | lines | 16/16 | 0/16 | +1.000 |
| `granite4-3b` | lines | 15/16 | 0/16 | +0.938 |
| `gemma3-1b` | lines | 11/16 | 0/16 | +0.688 |
| `qwen3-1.7b` | lines | 6/16 | 0/16 | +0.375 |
| `granite4-3b` | strict (span) | 4/16 | 0/16 | +0.250 |
| `granite4-3b` | minlen (span+rules) | 4/16 | 0/16 | +0.250 |
| `gemma4-31b` | lines **VOID** | 0/0 | 0/0 | — |
| `gpt-oss-20b` | lines **VOID** | 0/0 | 0/0 | — |

The two VOID rows are honest failures, not omissions: all 32 scored calls
returned HTTP 404 because the models were absent from the local Ollama instance.
The scorer refuses to report a dead run as a perfect zero.

Then rebuild the provenance cards:

```
python run_ledger.py      # -> measurements/RUN_LEDGER.md   (29 runs, 2,186 calls)
python paper_trail.py     # -> measurements/PAPER_TRAIL.md  (18 hand-traced cases)
```

`run_ledger.py` reads the result files themselves and remembers nothing. If a run
is not in the ledger, its output is not on disk.

---

## Layout

```
paper/            the submitted paper, the draft it was cut from, ten figures
harness/          the measurement code (10 scripts, engine-free by construction)
records/          34 raw per-call records + the frozen question manifest
results/          scored envelopes and the contract x model matrix
measurements/     five write-ups, the literature cross-check, the provenance cards
corpus_fixture/   redacted corpus, sufficient to re-run every citation check
```

---

## What is here, and what is not

This repository contains the **measurement harness** — the code which produced the
paper's numbers. It does not contain the FIT Engine itself, which is unpublished
work, and it does not contain the currency-layer measurement, whose inputs are
unpublished research material from a separate project. Every script here is engine-free, and that was checked properly rather than
assumed. An import-statement scan is not sufficient, because the engine was
loaded dynamically through `importlib.util.spec_from_file_location`: five
scripts reached it that way, two only transitively, and all five were withdrawn.
What ships is the closure reaching no engine module by either route.

`corpus_fixture/` needs explaining, because it is the one place the two aims
collide. The scorer does not trust a run's own summary — it re-reads the cited
lines and checks the evidence is really there. That check needs the corpus. The
corpus is an engine working directory, so publishing it whole would publish the
engine.

The fixture resolves this. Each of the nine indexed files is reproduced with its
line structure intact and every character replaced by a dot, **except** the text
already published verbatim in `records/` — the evidence tokens and the spans the
models actually quoted. Nothing is disclosed which a reader cannot already read
in the raw records.

The fixture is not an approximation. Scored against it, all eight rows of the
matrix are identical to the same scoring against the real corpus — verified cell
by cell. What it will not support is regenerating the question set, which needs
the original text; that is why the questions are shipped frozen as
`records/questions_seed0_n20.json`.

---

## Re-running against live models

Needs [Ollama](https://ollama.com) on `localhost:11434` and the models pulled.
All calls use `temperature: 0`, `num_predict: 400`, `stream: false`.

```
python run_attenuate.py granite4:3b 0 20 lines    # model, seed, n, contract
```

`run_attenuate.py` writes to `records/`. Contract variants are `strict` (quoted
span), `minlen` (span plus four explicit rules) and `lines` (first and last line
number). It needs a real corpus, not the fixture.

The payload-size envelopes in `results/` were produced by `calibrate.py`, which
is not in this release because it reaches the engine transitively. They ship as
data and the ledger reads them; they cannot be regenerated here.

Scripts quoting source text or generating questions — `heldout.py` and
`paper_trail.py` — refuse to run against the fixture rather than emit dots, and
say why. Point them at any real codebase:

```
set FIT_CORPUS=C:\path\to\your\repo        (Windows)
export FIT_CORPUS=/path/to/your/repo        (Linux, macOS)
```

The finding is not specific to this corpus. Any tree of text files will do.

Paths resolve from the repository by default and are overridable by
`FIT_CORPUS`, `FIT_RECORDS`, `FIT_RESULTS`, `FIT_MEASUREMENTS`, `FIT_QUESTIONS`.

### Hardware

Every number in the paper was produced on an Intel Core i5-8500T — six cores,
35 W, 8 GB RAM, integrated graphics unused. CPU only, no accelerator at any
point. Median seconds per call: `gemma3:1b` 10.3, `qwen2.5-coder:3b` 15.4,
`granite4:3b` 17.1, `qwen3:1.7b` 44.4.

---

## Two harness errors worth reading

The paper argues automated probes interrogate the scorer, so a defective scorer
is invisible to them. Both defects below survived every probe and were found by
hand-tracing cases. Both are documented in full, with their fixes, in
`measurements/measurement_16_lines_contract.md`.

**D9** — the evidence clause read `q.get("token")` where the question key is
`tok`, so it silently never ran. The first write-up reported 16/16 verified and
16/16 false affirms. The truth was 15/16 and 0/16.

**D8** — the attenuation loop always called the span parser, voiding the
line-number arm of that measurement.

Both are fixed here. `score_contracts.py` now also exits with an error rather
than scoring every row 0/16 when the corpus or question manifest is missing —
the same failure mode, caught once more during packaging.

---

## Revision history

This repository was public before the paper was final. Changes made since it
first went up are recorded here rather than applied quietly. A correction
nobody can see reads to a later reader as though the file had always been
right, which is the failure this project is about.

### 7 November 2026

**Integrity fix — `harness/refresh_cards.py`.** The script printed *"this script
will not edit a card a human wrote"* and then copied the two hand-written
continuity cards over the canonical copies, silently reverting any correction
made there. Its audit read the source copy, so it never checked the card a
person actually edits. Two corrections were destroyed this way and recovered
only because they were re-checked afterwards. Fixed: the hand-written cards are
no longer published by the script, and the audit now reads the canonical copy.
Adds `--archive <session folder>`, which files the outgoing state card under a
SUPERSEDED header. No measurement depends on this script; no table or figure
changes.

**Paper, sections 2 and 10.** Section 2 described the framing's falsification
condition as untested. It had in fact been run — a four-phase deliberation arm
beside the direct one, 96 calls on `gemma3:1b` — and the attribution errors did
not yield to deliberation, so the framing survived its own refutation test.
Section 10 had reported the framing's two further predictions as both failing;
it now separates them, because the load prediction fails and the deliberation
prediction holds. The confound is stated with both: the deliberation arm also
degraded output format.

**Two file paths removed**, from `measurements/measurement_12_verification_floor.md`
and `measurements/measurement_14_falsifiable_test.md`. Each named a location in
the author's private work tree. The claims they support are unchanged.

### 10 November 2026

**Section 9 of the paper** now says both defects are in the harness rather than
the engine, and names `measurements/measurement_16_lines_contract.md` as the
file documenting each with its fix. The labels, the numbers and every figure
are unchanged.

**Three counts in this README corrected** — 34 raw run records rather than 35,
and the `paper/` and `measurements/` layout lines now name every file they
hold.

---

## Licence and citation

Apache License 2.0 — see `LICENSE`.

Repository: <https://github.com/Constantinos999/fit_engine_probe>

> Eleftheriou, C. (2026). *Misbinding, not fabrication: attribution error in an
> offline developer agent.* Kaggle, Google — Gemma 4 Developer Agent, Paper Track.
