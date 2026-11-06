# Measurement 12 - the verification floor

30 October 2026. `calibrate.py qwen3:1.7b`, 112 calls, 1 timeout, run on the
user's own machine (8 GiB, no GPU).

## The headline the screen gave, and the number the full run gave

The 16-call screen reported separation **+0.62** at 1,200 chars. The full
112-call calibration reports **+0.44**. The screen was optimistic by 0.18 -
eight questions against sixteen, and a different seed.

This is the sixth time in this project a headline has been revised by a control
run. It is the first time the control was already in the protocol rather than
thought of afterwards: the standing rule "confirm any screen pass with full
calibrate.py" existed before the screen was run. The pattern has not stopped;
it has been made routine, which is the only available defence.

## Result

| tier | verify hit | false-affirm | separation | informative |
|---|---|---|---|---|
| 400 | 16/16 | 11/16 = 69% | +0.31 | yes |
| **1,200** | 16/16 | 9/16 = 56% | **+0.44** | yes |
| 3,600 | 14/16 | 11/16 = 69% | +0.19 | **no** |

The calibrator's verdict: `selection: model`, **`verification: false`**. At 56%
false-affirm more than half of wrong files are still affirmed, so `qwen3:1.7b`
is not a verifier. It is the best local result this project has produced and it
is still not sufficient.

Two details behind the number:

- **Its usable window is <= 1,200 chars.** At 3,600 it begins refusing when the
  evidence IS present - 2 false NONEs of 16, a failure mode absent at the two
  smaller tiers.
- **It fabricates.** 3 of 48 false-affirm probes named a file that was never
  shown (1 at 1,200, 2 at 3,600). Every routing error in measurement 8 was a
  swap, with zero fabrications, which is why a deterministic existence check
  was worthless there. Against this model it would catch something. The guard's
  value is model-dependent, not absolute.

## Selection: the first local model to beat arithmetic

`index_select` **7/16, against the deterministic word-overlap ranker's 4/16.**
Every previous local model tied or lost to the ranker (`gemma3:1b` 3 vs 3).

The ranker scores 4 here and 3 in the three earlier envelopes because the
tokeniser fix (splitting on underscores) has landed - a change made on
structural grounds when it was a no-op on this corpus. It is no longer a no-op.

## Where the floor actually is

| model | params | separation (best tier) | selection | latency |
|---|---|---|---|---|
| `gemma3:1b` | 1.0B local | +0.00 | 3/16 | 2.9 s |
| `qwen3:1.7b` | 1.7B local | +0.44 | **7/16** | 26.0 s |
| `qwen2.5-coder:3b` | 3B local | +0.38 (screen) | not run | ~6 s |
| `gpt-oss:20b` | 20B cloud | +1.00 | 11/16 | 5.4 s |
| `gemma4:31b` | 31B cloud | +1.00 | 11/16 | 0.5 s |

**The floor is a cliff, not a slope.** Between 1.7B (+0.44) and 20B (+1.00)
there is nothing measured, and the two cloud models are not partially capable -
they are at 1.00, hit 100% and false-affirm 0% at every tier. Nothing in the
consumer band is partially usable either: 1B is at zero, 1.7B and 3B sit in the
dead zone where they answer more wrong files than they refuse.

Parameter count does not order this list cleanly. 1.7B beats 3B on separation
and 20B matches 31B. What the capable models share is not size but
post-training that permits refusal.

## What it costs to have refusal locally

26.0 s median per call - 9x `gemma3:1b` (2.9 s) and 52x `gemma4:31b` (0.5 s),
because it emits reasoning tokens before answering. One call timed out and cost
a question. On a machine with 0.9 GiB free of 7.8 GiB, this is at the edge of
what will run at all.

## Architecture consequence

The best available offline configuration is now: **local model selection
(7/16), no verification**. Verification cannot be done locally by any model
screened. Combining qwen3's selection with remote verification would give 7/16
answered at zero misattributions - remote verification is measured at hit 100%,
false-affirm 0%, so it keeps the 7 correct and converts the 8 swaps to NONE.
Against measurement 8's remote-select-and-verify at 31/48 (~10.3/16), local
selection trades about three answers per sixteen for one fewer remote call per
query. NOT YET MEASURED END TO END - derived by composing two measured stages
on overlapping but not identical question sets.

**The offline claim still does not hold.** A corpus-resident agent can now
SELECT better than arithmetic on consumer hardware. It cannot yet CHECK itself
there, and checking is the half that produces the zero-misattribution
guarantee.


---

# Part 2 — granite4:3b. The floor is at 3B, and it is local.

`calibrate.py granite4:3b`, 112 calls, **zero errors**, same generated question
set as every other envelope (seed 0, n=16), run on the user's own machine.

| tier | verify hit | false-affirm | separation |
|---|---|---|---|
| 400 | 16/16 | 1/16 | +0.94 |
| **1,200** | **16/16** | **0/16** | **+1.00** |
| 3,600 | 15/16 | 3/16 | +0.75 |

`verification: true`. **A 3B model running locally verifies at the same
separation as the 31B cloud model.** This is the result the project has needed
since the offline claim was first written down.

## It is not the degenerate solution

A model that answers NONE to everything also scores 0% false-affirm. This one
does not: on `verify_hit_1200` its sixteen correct answers are spread evenly
across four different files — `local_runner.py`, `notes.md`,
`subsystem_daemon.py`, `fit_engine.py`, four each. It identifies; it does not
default. On `verify_fa_1200` it answers NONE sixteen times out of sixteen.

## It fabricates at 3,600, and the envelope was wrong because of it

Three times — twice on false-affirm probes, once on a hit probe — it answered
`memory_inject.md`. **That file does not exist in the corpus.** All three
occurrences are at the 3,600-char tier; there are none at 400 or 1,200.

The shipped envelope said `max_bytes_per_object: 3600`, because the calibrator
required only `separation >= 0.5` and 3,600 scores +0.75. **Separation does not
exclude invention.** A swap names a real file and can be caught by ranking; a
fabrication cannot, and must be caught by existence. `calibrate.py` now requires
a tier to both separate AND not fabricate before it can be the byte cap:

```python
fabricating = {t for t in SIZE_TIERS
               if any(r.get("cls") == "fabrication" and r.get("tier") == t
                      for r in rows)}
tolerable = [t for t in SIZE_TIERS if sep[t] >= 0.5 and t not in fabricating]
```

Re-derived across all five envelopes from their saved rows: **only
`granite4:3b` was affected** — 3,600 → **1,200**. The two cloud models fabricate
at no tier, which is consistent with measurement 8, where all 16 routing errors
were swaps and none were inventions. The correction is recorded in the envelope
itself rather than silently applied.

## Selection and verification are separate faculties

| model | selects (of 16) | verifies |
|---|---|---|
| `gemma3:1b` | 3 | no (+0.00) |
| `qwen3:1.7b` | **7** | **no** (+0.44) |
| `granite4:3b` | 5 (refuses 11) | **yes** (+1.00) |
| `gpt-oss:20b` | 11 | yes |
| `gemma4:31b` | 11 | yes |

The two local models invert each other. `qwen3:1.7b` is the better selector and
cannot verify; `granite4:3b` verifies perfectly and refuses to select on 11 of
16. Neither is "better" — they are good at different jobs, and the engine asks
two different questions. This is direct evidence for the architecture the
project arrived at by other means: **selection and verification are separate
stages and should not be asked of the same component.**

## What is NOT established

- **Latency is unknown.** `calibrate.py` records no per-call timing, unlike
  `screen_verifier.py`. Harness defect **H6**. The whole economic case for a
  local verifier turns on seconds per call and this run cannot supply it. A
  16-call screen would.
- **Not measured end to end.** Composing a selector with this verifier should
  give zero misattributions offline, because the verifier is measured at hit
  100% / false-affirm 0% at 1,200 chars. That is a composition of two measured
  stages, not a measurement. Measurement 8 re-run with `granite4:3b` as the
  verifier would settle it, and it needs no cloud calls at all.
- One question set, one seed, 16 questions, one corpus of nine files.

## Consequence for the offline claim

Stated honestly: **an agent can now select and check itself on consumer
hardware.** The checking half — the half that produces the zero-misattribution
guarantee and the half that has been missing all project — exists at 3B,
offline, at cloud-model separation. The engine's remaining dependency on a
remote tier is for *selection quality* (11/16 against 5–7/16), not for honesty.


---

# Part 3 — an external code review of calibrate.py, verified claim by claim

31 October 2026. A review of `calibrate.py` was produced by another model
without access to the sibling modules or the saved runs. Each claim was checked
against the source and against the 1,803 saved rows before being accepted.

## Confirmed, and load-bearing

**The guard never saw the verification rows.** `guard.finish()` filtered on
`r["arm"] in ("index_select", "verify_hit")`, but the hit arms are named
`verify_hit_400 / _1200 / _3600`. The literal never matched. Measured: the guard
received **16 rows of the 64** it should have. Every measurement the envelope
recommends on ran unguarded. The reported numbers are not wrong — they were
recomputed independently from the raw rows — but the file's stated safety
property was not in force.

**A guard failure destroyed the run.** `guard.finish()` at line 163, the JSONL
write at line 233. An invariant raising after 112 calls lost everything. Rows
are now written first, and the path is printed before the guard runs.

**Errored calls sat inside the rates, and this one moved a published number.**
`gpt-oss:20b` was reported at **+0.94** separation at 3,600 chars. That tier
contains exactly one failed call — `URLError: Tunnel connection failed: 502 Bad
Gateway` — classified `malformed` and counted as a false affirmation. Excluding
it, the tier is **+1.00**. *A network fault was published as a model limitation.*
`qwen3:1.7b` likewise has one timeout in `index_select`, so its selection score
is 7 of 15 usable calls, not 7 of 16.

## Confirmed in the code, but moved nothing

- **Asymmetric scoring.** The baseline is scored against all evidence homes, the
  model against the first only. True at lines 101 and 128 — but every question
  in the generated set has exactly one home, so no question was ever scored
  asymmetrically. Latent.
- **verification / max_bytes contradiction.** `verification` was computed from
  separation alone, so `verification: true` with `max_bytes: null` was
  reachable. Checked all five envelopes: it never occurred. Now prevented —
  `verification` requires a tolerable tier to exist.
- **Progress counter** printed `[112/80]`. Display only.

## Found during verification, not in the review

**No envelope could regenerate its own question set.** `qset` recorded
`n={len(qs)}` — the questions that *survived* generation — not the `n` that was
requested. Every envelope read `seed=0 n=16`, but `generate(n=16)` returns 12;
the runs used the default `n=20`, which returns 16. For a file whose purpose is
to be the machine-readable record of a measurement, that is the second most
serious defect after the guard. Now recorded as
`requested_n=<n> returned=<len(qs)>` plus explicit `n_requested` and `seed`
fields. The five existing envelopes carry `n_requested: null` and say so,
because the value is not recoverable after the fact.

## Effect of all fixes, re-derived offline from the saved rows

No model calls. Rows carry everything needed.

| model | selection | separation | verification | max_bytes |
|---|---|---|---|---|
| `gemma3:1b` | 3/16 → 3/16 | +0.00 → +0.00 | false | null |
| `gemma4:31b` | 11/16 → 11/16 | +1.00 → +1.00 | true | 3600 |
| `gpt-oss:20b` | 11/16 → **11/15** | +1.00 → +1.00 | true | 3600 |
| `granite4:3b` | 5/16 → 5/16 | +1.00 → +1.00 | true | 1200 |
| `qwen3:1.7b` | 7/16 → **7/15** | +0.44 → +0.44 | false | null |

**No conclusion changes.** Exactly one per-tier value moves: `gpt-oss:20b` at
3,600 chars, +0.938 → +1.000. The figure is re-rendered accordingly.

## Cross-tool audit — are these defects patterns?

The two real defects were checked across all 15 tools, since a defect found once
is worth looking for everywhere.

- **Label-equality against prefixed names: unique to `calibrate.py`.** No other
  tool builds an f-string label and then compares it by equality.
- **Errors inside rates: latent in four tools** (`probe_fit.py`,
  `probe_chunked.py`, `probe_perobject.py`, `screen_verifier.py`) — they record
  an error field and never filter on it. But across **every saved run — 1,803
  rows — there are only 3 errored calls**, all of them in the two calibrate runs
  already corrected. No other reported number is affected.

Worth hardening before the Armadillo corpus runs, where the corpus is larger and
timeouts are likelier, but nothing to re-run today.

## What the review got wrong, and why it matters

Two of its six "real bugs" had no effect, and its specific prediction about
`granite4:3b` — that the fabrication rule would emit `verification: true` with
`max_bytes: null` — did not occur, because granite's best tier is the
non-fabricating one. The reviewer said as much itself: without the sibling
modules and the runs, it could flag but not confirm. **The claims were worth
exactly what checking them cost, which was about twenty minutes of arithmetic
over files already on disk.** The one it found that mattered — a 502 published
as a model limitation — would not have been found any other way.


---

# Part 4 - CORRECTION: the "fabrication" was not invention

31 October 2026. Found while reading `C:\.fit_engine_AI_Plan\Claude_fit_engine_mod.docx`,
a design note that names `staging/memory_inject.md` as the FIT subsystem's payload
file. Verified immediately afterwards.

## What was claimed

Measurement 12 Part 2 reported that `granite4:3b` "fabricates filenames not in the
corpus", answering `memory_inject.md` three times, and `calibrate.py` was patched
so a tier that fabricates cannot set `max_bytes_per_object`.

## What is actually true

`staging/memory_inject.md` **exists in the workspace**. It is referenced in **six
of the nine indexed corpus files** - `fit_engine.py`, `fit_engine.py.old.txt`,
`local_runner.py`, `notes.md`, `run_test.py`, `subsystem_daemon.py` - eleven times
in total. `heldout.read_corpus()` excludes the `staging` directory, so the file is
in the workspace and absent from the index the answer is scored against.

The mechanism is exact. Both models produced the SAME single string and no other:

| tier | windows whose text mentions `memory_inject` | granite4:3b | qwen3:1.7b |
|---|---|---|---|
| 400 | 0/16 | 0 | 0 |
| 1,200 | 1/16 | 0 | 1 |
| 3,600 | 9/16 | 3 | 2 |

The rate tracks window exposure to the string. **The models read a real filename
out of the text they were shown and named it.** That is not invention.

## What changes, and what does not

**Unchanged:** the errors are still errors. A model shown the wrong file and
answering `memory_inject.md` should have answered NONE. Separation at 3,600 is
still +0.75 for granite, and capping `max_bytes_per_object` at 1,200 still holds
on separation grounds alone.

**Changed, and it matters:**

1. **"Fabrication" was measuring corpus scoping, not model honesty.** The
   existence check was flagging a mismatch between the workspace and the index.
   An earlier conclusion - that the existence check "has value against qwen3
   because it fabricates" - rested on that misreading.
2. **The closed world was never stated to the model.** The prompt shows one file
   and asks which file answers the question; nothing tells the model that only
   indexed files are admissible. Naming a referenced file is not obviously wrong
   behaviour under that contract.
3. **Fabrication-as-a-class is now unevidenced in this project.** Across 1,803
   saved rows there is no case of a model inventing a filename that appears
   nowhere. Every error on record is a swap - to a real indexed file, or to a
   real excluded one.

## Consequence for the attenuation design

`check_existence` must say which world it is checking. Three options, and the
choice is a design decision rather than a bug fix:

- index the workspace fully, so the check matches what the model can see;
- state the closed world in the prompt (`answer with one of: ...`), making an
  out-of-index name a genuine contract violation;
- keep the exclusion and add a third verdict - `out_of_index` - distinct from
  both `exists` and `fabrication`, so the receipt says what happened.

The span check is unaffected: a span quoted from the shown file still verifies
against that file regardless of which world the filename lives in.

## Why this was missed

The classifier had a `fabrication` label and the answer matched its definition -
not in the corpus index. Nothing checked the definition against the workspace.
It took reading a design document that happened to name the file. The same shape
as every other correction in this project: a label applied correctly by a rule
whose scope was never verified.
