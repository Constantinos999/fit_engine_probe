# Measurement 14 - the predecessor's falsifiable test, run

31 October 2026. No new model calls; computed over every row this project has
saved (1,754 classified outcomes across 12 runs and 5 models).

*Corrected 11 November 2026 — this read "15 runs". That count included three
16-call screen records, which carry no classification and are not among the
1,754. The twelve records carrying a `cls` field sum to exactly the table below.*

## The test, as it was set

From `Claude_SCi_AI FIT.docx`, written before any of this project's measurements
existed:

> If an agent's attribution errors are genuine misbindings, their rate should
> rise with the number and the mutual similarity of retrieved items and with
> adjacency between them, and should be largely insensitive to additional
> deliberation, while fabrication rate falls with it. ... If more thinking fixes
> your attribution errors, they were not misbindings and this framework is the
> wrong lens.

The decomposition it asked for is Bays, Catalao & Husain 2009: separate an
answer into CORRECT, SWAPPED to a retrieved non-target, and GUESSED/fabricated,
because binary scoring collapses two failure modes with different causes.

## Result

| outcome | n | share |
|---|---|---|
| correct | 1,178 | 67.2% |
| **swap** (real file, wrong one) | **382** | **21.8%** |
| malformed | 87 | 5.0% |
| refusal (NONE) | 59 | 3.4% |
| ambiguous | 30 | 1.7% |
| skipped | 10 | 0.6% |
| fabrication | 8 | 0.46% |

And every one of those 8 dissolves on inspection. They are two distinct strings:

- `memory_inject.md` x6 - exists at `staging/memory_inject.md`, referenced in
  six of the nine indexed corpus files, excluded from the index by
  `read_corpus()`.
- `motif_specificity_test.py` x2 - a real file in the author's wider work tree,
  outside the indexed corpus, and named explicitly inside `notes.md`, one of the
  nine files the model was shown.

**Genuine fabrication across 1,754 classified outcomes: zero.**
Every error this project has ever recorded is a misattribution of a real file.

## What that licenses, and what it does not

**Licensed.** The error class the framework predicts is the error class that
occurs, and the alternative it was contrasted against is empirically absent. A
binary right/wrong eval would have scored 382 swaps and 0 fabrications
identically - 576 "wrong" answers with no indication that they share a single
cause. The decomposition was worth performing.

**Not licensed.** This is not proof the mechanism is binding. Two of the
prediction's other legs are unconfirmed:

- *Rate rises with number of retrieved items.* Measurement 6 varied object count
  (6 / 2 / 1 files per call) and found 1/16, 10/16, 2/16 - not monotonic, and
  the k=2 advantage did not survive shuffling which files were paired (5/24
  pooled). One object per call, the maximal-suppression condition, was among the
  worst.
- *Insensitive to additional deliberation.* Within the two models that record
  per-call timings, wrong answers arrived FASTER than right ones
  (`qwen2.5-coder:3b` 11.8 s vs 13.3 s; `qwen3:1.7b` 22.9 s vs 26.7 s, n=5 and
  n=3). That is the opposite direction, weakly. And `qwen3:1.7b`, which emits
  reasoning tokens before answering, still fails to verify at +0.44.

So the central prediction holds and two subsidiary ones are unsupported or point
the other way. The honest summary is that the ERROR TAXONOMY transferred and the
LOAD MODEL has not been demonstrated.

## The constraint the Armadillo corpus confirmed at scale

Constraint 5 was "identity must survive change" - from the object-file result
(Kahneman, Treisman & Gibbs 1992), an investigation ledger keyed by path or
content hash misses on renames and moves, precisely where re-research is most
wasteful.

Project Armadillo is that failure, at scale, in a real archive. File numbers
44-64 are cited 46 times by 17 live units and cannot be resolved by any tool,
because identity was assigned by FOLDER NAME and the documents outside numbered
folders never received it. The banner campaign covered folders 65-94 only. The
citation was never broken; the identifier scheme was.

A prediction made from 1992 psychology, borne out in six months of bioinformatics
notes.

## The constraint our data argues with

Constraint 3 was "budget in entities, not tokens" (Luck & Vogel 1997 - capacity
is in bound objects, conjunctions stored at no extra cost). Our measurements put
the operative variable on the other axis: separation varies sharply and
monotonically with CHARACTER window at fixed object count (granite4:3b +0.94 /
+1.00 / +0.75 across 400 / 1,200 / 3,600), while varying object count at fixed
budget produced an effect that did not survive shuffling. On this corpus, with
these models, the token budget is measuring something real and the entity budget
is not yet shown to.
