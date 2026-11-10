# Misbinding, not fabrication: measuring attribution error in an offline developer agent

### Why citation format, not model size, decides whether a small local agent can be trusted with a research record

**Constantinos Eleftheriou**

## Abstract

An agent working offline on consumer hardware must do more than fit in memory:
it must not attribute a fact to the wrong file. Across **1,754 classified outputs** from five models (1B-31B), **genuine
fabrication was zero**; 21.8% were **swaps** — a real file, the wrong one.
Misbinding, not invention, which makes it checkable. The *format* demanded dominates: a quoted text span, forcing the model to escape
characters inside a JSON string, yields 4/16 verified citations; integer line
numbers yield 15/16 from the same model on the same questions. Across four models from three vendors (1B-3B) under the line-number contract,
yield ranges 6-16 of 16 while **false attribution is 0/16 in every case**:
capability determines how much the system answers, not how often it is wrong.
All measurements ran CPU-only on an 8 GB office desktop.

## 1. Introduction: the problem is not hallucination

A developer agent working across a large repository makes two errors which
evaluation collapses into one: it can **fabricate** — assert a fact existing
nowhere — or **misbind**, reporting a true fact as belonging to the wrong file,
function or version. Binary scoring records both as "incorrect", though causes
and remedies differ.

The distinction matters more for an agent than a chatbot, because misbinding
*manufactures authority*: a fabricated claim tends to fail its first contact
with a compiler, while a true value attributed to the wrong file passes every
check and is trusted by the next session.

Our motivating case is a six-month genomics project of 818 files in which
settled results were repeatedly re-derived because nothing said which were
current — the failure a coding agent has on a large repository: information
present, retrievable, misattributed. We measured the two classes separately, built an agent around the distinction
following Treisman's Feature Integration Theory (§11), and ran controls against
our own claims.

The measured corpus is source: nine Python modules, with questions asking which
file holds a given line. The contract we arrive at — cite
`{file, first_line, last_line}`, then read those lines back — is the primitive
this competition's harness exposes as `read_file(path, start_line, end_line)`.
Our result says what it is worth: for a 3B model, the difference between citing
verifiably 4 times in 16 and 15.

## 2. Misbinding is essentially the whole of it

We adopted the three-component decomposition from visual working memory (Bays,
Catalao and Husain, 2009): **correct**, **swapped** to a non-target item, and
**guessed**. For an agent's citations: correct attribution, a real file which is
the wrong one, and a file which does not exist.

Across **1,754 classified model outputs** — 15 runs, 5 models, 1B to 31B
parameters:

| outcome | n | share |
|---|---|---|
| correct | 1,178 | 67.2% |
| **swap — a real file, the wrong one** | **382** | **21.8%** |
| malformed | 87 | 5.0% |
| refusal (NONE) | 59 | 3.4% |
| ambiguous / skipped | 40 | 2.3% |
| fabrication | 8 | 0.46% |

The eight apparent fabrications did not survive inspection: six named a file
excluded from the index by a directory filter but referenced in six of the nine
indexed files, two named a file printed inside a file the model was shown.
**Genuine fabrication: zero.** Every error we have recorded is a misattribution of
a real file.

Two consequences follow immediately. First, a deterministic existence check —
"is this filename real?" — would have caught nothing. Second, binary scoring
would have reported 576 wrong answers with no indication 382 of them share a single cause.

A swap is an **illusory conjunction** in a text corpus (§11): the fact is read
correctly and bound to the wrong source. We state what would refute this — if
extra deliberation repaired the errors, they were never binding failures and the
framing should go. We ran the arm. A four-phase deliberation prompt on the 1B
model left swaps at 6 of 16 on the bound payload, unchanged, and raised them
across all three arms from 8 to 10 of 48. The errors did not yield to thinking
harder. We hold the test weak rather than decisive, because the same arm also
degraded output format — malformed replies rose from 2 to 6 of 16 — so part of its
failure to help belongs to the scaffold, not to the model.

## 3. An architecture which survived its controls

If the dominant error is misbinding, the defence is verification against the
source. We compared routing policies over 48 questions across three seeds,
ranking deterministically and asking the model only to confirm:

| policy | answered | misattributions | model calls/query |
|---|---|---|---|
| local only | 9/48 | 9 | 0 remote |
| remote select | 31/48 | 15 | 1 |
| **remote select + verify** | **31/48** | **0** | ~1.9 |

Per seed the misattribution column reads 4 → 0, 6 → 0, 5 → 0. The narrowness is the finding — **verification adds no answers.** It converts
confident wrong answers into honest refusals: accuracy among answers given rises
from 67% to 100% while coverage does not move. For an agent whose output enters
a durable record, this is the trade worth making. The same experiment refuted
escalating only verification (4/16, capped by the ranker's top-1 recall) and
local-only operation (9/48).


## 4. Capability is not predicted by size, so it must be measured

Verification is not a capability every model has. We defined **separation = hit
rate − false-affirmation rate** at matched payload sizes: the model is shown one
file containing the evidence and one which does not, at 400, 1,200 and 3,600
characters. A model naming whatever it is shown separates at zero. The result
goes to `envelope_MODEL.json`; the engine routes on this file, not on
assumptions.

Payload size is a variable, not a detail. `granite4:3b` separates +0.94 at 400
characters, **+1.00 at 1,200** and +0.75 at 3,600, false affirmation rising
0.000 → 0.188. Performance is not monotonic in context: there is an optimum, and
text past it makes the model *less* able to tell right file from wrong — hence
per-model `max_bytes_per_object`.

![Figure 1](fig1_verification_floor.png)

**Figure 1.** Left: separation against window size; the shaded band is the
usable-verifier region. `granite4:3b` is the smallest model entering it and the
only local one; its fall at 3,600 characters comes from answering a real file
outside the index, not invention. Right: selection accuracy.

| model | selection | separation | verifies |
|---|---|---|---|
| gemma3:1b | 3/16 | +0.00 | no |
| qwen3:1.7b | 7/15 | +0.44 | no |
| granite4:3b | 5/16 | +1.00 | **yes** |
| gpt-oss:20b | 11/15 | +1.00 | yes |
| gemma4:31b | 11/16 | +1.00 | yes |

Transport failures are excluded from every rate. A 20-line ranker is the floor
at 4/16; only the two largest beat it decisively.

**Parameter count does not order the table** — a 1.7B separates better than a
3B, a 20B matches a 31B — and nor does latency. A 3B on an 8 GB desktop with no
GPU reaches the separation of a 31B. What the capable models share is not scale
but post-training permitting refusal: the ability to say *no*.

## 5. Structured output costs a small model its refusal

To make a verifier's answers checkable without a second model, the agent was
asked for `{"file": ..., "span": "TEXT VERBATIM"}`, checked by literal
containment. It failed instructively.

| | bare filename | JSON span |
|---|---|---|
| refusals, wrong-file arm | **16/16** | **2/16** |
| false-affirmation rate | **0.000** | **0.875** |
| spans verified | — | 6/16 |

The model verifying at +1.00 affirmed the wrong file 14/16 under a schema.

The mechanism is specific. Five failed spans were fragments — `print(f`, `item[`
— and all five stop at **exactly the character requiring escaping inside a JSON
string**: in each case the next source character is a double quote. The model is not skimming. Under schema-constrained decoding it cannot
emit an escaped quote inside a string, so it truncates.

A prompt control adding four explicit rules — one complete line, 30+ characters,
no joined lines, no placeholders — changed nothing: 6/16 verified in both arms by literal
containment, 4/16 once the evidence clause is enforced as in §6, the same
eight of ten failures, fragments byte-identical. Refusals dropped to 1/16.

Constrained decoding is documented to degrade reasoning. What we observe is
narrower and, for an agent, worse: **the casualty is the refusal option.** A
schema removes the cheapest honest output. Classification survived — the right
file was named 16/16 in every arm — the ability to decline did not.

**We state the limit of this claim.** The refusal collapse is measured on one
model, across the bare, span and span-plus-rules contracts. We have not run a large model under the same
contracts, so we cannot fully separate "the schema caused the collapse" from
"the schema exposed a small-model limitation". Fan (2026) reports the latter
mechanism directly (§11), which makes the distinction a real one rather than a
hypothetical. It matters less for the remedy than it might: the matrix below
shows two 3B models from different vendors reaching 16/16 and 15/16 under the
line-number contract, so whichever mechanism dominates, the format change is
what recovers the capability at this size.

## 6. The contract across models

The same sixteen questions, the same corpus, temperature 0, three model families
and three sizes. `citation verified` counts answers whose citation passes the
engine's own deterministic check with the evidence clause enforced; `false affirm` is the same check applied to the wrong-file arm.

| model | params | citation verified | false affirm | separation |
|---|---|---|---|---|
| `qwen2.5-coder:3b` (Alibaba) | 3B | **16/16** | **0/16** | **+1.00** |
| `granite4:3b` (IBM) | 3B | 15/16 | **0/16** | +0.94 |
| `gemma3:1b` (Google) | 1B | 11/16 | **0/16** | +0.69 |
| `qwen3:1.7b` (Alibaba) | 1.7B | 6/16 | **0/16** | +0.38 |

![Figure 2](fig2_contract_matrix.png)

**Figure 2.** Left: verified citations and false attributions under the
line-number contract, four models, 16 questions each. Right: one model, three
citation formats. Two things are visible, the second mattering more.

**Yield varies with the model**, 6 to 16 of 16. Two 3B models from different
vendors reach 16/16 and 15/16 while the 1.7B from the stronger one's own family
reaches 6/16, so the effect tracks capacity and specialisation, not vendor. The
same `granite4:3b` scores 4/16 when the citation must be quoted as text instead
of cited by line, isolating the format effect.

**Safety does not vary at all.** Every model, size and family: **zero false
affirmations in sixteen attempts** — not because the models refused (under this
contract they essentially never do) but because every wrong answer produced a
citation failing a function containing no model. A 1B which could veto nothing
under a bare-filename contract (+0.00) misattributes nothing here.

The architectural claim, as sharply as the data allows: **capability determines
how much the system can answer, not how often it is wrong.** That separation is
what makes a 1B model usable on ordinary consumer hardware where misattribution
is unacceptable.

## 7. Measurement setup

One office desktop: **Intel Core i5-8500T** (6 cores, 35 W), **8 GB RAM**,
**Intel UHD Graphics 630** integrated and unused — every number is CPU-only.
Models were served locally by **Ollama** over `POST /api/generate`, default tags:

| tag | digest | size |
|---|---|---|
| `qwen2.5-coder:3b` | `f72c60cabf62` | 1.9 GB |
| `granite4:3b` | `89962fcc7523` | 2.1 GB |
| `qwen3:1.7b` | `8f68893c685c` | 1.4 GB |
| `gemma3:1b` | `97558784bdc9` | 806 MB |

Every call used `temperature: 0`, `num_predict: 400`, `stream: false` and
Ollama's `format` parameter carrying the contract schema — `{file, span}`, or
`{file, first_line, last_line}` with both line fields typed as integers. The
window was the calibrated `max_bytes_per_object`, 1,200 characters throughout,
centred on the evidence rather than taken as a prefix.

Analysis, scoring code and drafting used Claude Science (Claude Opus 5, Pro
plan); every figure was computed by code from saved raw records.

Median s/call, 48 calls each:

| model | median s/call | run |
|---|---|---|
| `gemma3:1b` | 10.3 | 10.1 min |
| `qwen2.5-coder:3b` | 15.4 | 15.9 min |
| `granite4:3b` | 17.1 | 18.0 min |
| `qwen3:1.7b` | 44.4 | 45.1 min |

`qwen3:1.7b` is slowest despite being second smallest because it emits reasoning
tokens first — an output habit, not size. The matrix cost ninety minutes.

Two cloud runs (`gemma4:31b`, `gpt-oss:20b`) failed with HTTP 404 on all 32
scored calls — the models were absent. Reported VOID, not zeros; the
capacity-versus-format control remains outstanding.

## 8. Method: no claim ships without a check containing no model

The governing rule emerged from repeated failure: five headline results were
overturned by controls which were cheap, obvious in hindsight, and run after the
claim was written. Reported as results, because they are:

- A retrieval improvement credited to a small model was matched by a 20-line
  ranker.
- A binding advantage at two objects per call (10/16 vs 1/16) collapsed to 5/24
  under shuffled file pairing — the effect was the pairing.
- Four corpus-specific phrases in a parser's regex were ablated; recall held
  8/8.
- A +0.94 at the largest payload was one HTTP 502 counted as a false
  affirmation. Corrected to +1.00: a network fault read as a model limit.
- A defect treating a refusal as proof of absence was documented, reintroduced
  fourteen hours later, and caught only end-to-end.

The fifth matters most to anyone building a harness: a module passing 19 of 19
self-tests can still hold a loop discarding correct answers.

The discipline is not specific to this corpus or these models. **Before trusting
any aggregate, hand-trace twenty real cases spread across the failure classes,
not the first twenty.** Automated probes interrogate the scorer, so a defective scorer is invisible to
them: the scorer defect in §9 survived every probe and would have been caught on
case one. Retain the per-call records so cases the authors did not choose can still be
re-selected: the defence against selection bias is not the author's care but the
evidence surviving in a form someone else can check.

## 9. Provenance, and what we got wrong

Two defects were found by hand-tracing, *after* the result was written up. Both are in the harness, not the engine; `measurements/measurement_16_lines_contract.md` in the repository documents each in full, with its fix.

**D9**: the scorer requested the evidence token with `q.get("token")` while the
question dictionary emits `tok`. `get()` returned `None` every time, so the
verifier skipped its evidence clause and scored any valid line *range* as
verified — which it always is. The first write-up reported 16/16 and 16/16: what
looked like a verifier with no teeth was a scorer with none. Re-scored from the
same replies: 15/16 and 0/16.

**D8**: the attenuation loop accepted a `variant` argument but parsed every
reply with the span parser regardless, so the line-number contract — which
returns no text span — failed every check and attenuated all sixteen questions
to NONE. Wiring, not a finding.

Neither crashed, neither warned, both flattered the result, both invisible to
the probes — which asked the scorer, and the scorer was wrong. Every figure derives from a saved JSONL of raw outputs, one row per call;
envelopes re-derive from those rows with no model calls, exercised after four
calibrator defects with no conclusion changed. The defects above were found by reading rows against the files on disk, which
is why we keep eighteen hand-traced cases alongside the aggregates, and why
every rate here is recomputed from raw per-call records rather than read from
any run's own summary.

Errored calls have twice been allowed inside rates here: one HTTP 502 turned
+1.00 into +0.94, and two arms scored a tidy 0/16 while never running.

## 10. Limitations

The probe corpus is nine files; the question set is one generator at one seed
for most runs, 16 per envelope, so one question is 6 percentage points. The
orchestrating assistant was not measured: it read the corpus during analysis, so
any score would reflect conversation memory, not the payload.

The framing makes two further predictions: attribution errors should rise with
the number and similarity of retrieved items, and should resist deliberation.
**The first fails here.** Objects per call gave 1/16, 10/16 and 2/16 — not
monotonic — and the advantage did not survive shuffling. Wrong answers also
arrived *faster* than right ones. The second survives a weak test (§2). We claim
the taxonomy transfers, and nothing about the load mechanism.

Finally the offline claim is partial: retrieval and verification run locally at
cloud-model separation, but the zero-misattribution routing result cost a remote
call per query.

## 11. Related work

**Binding and illusory conjunction.** Treisman and Gelade (1980) separate
parallel feature registration from attentional binding and predict illusory
conjunctions where attention is insufficient; we take the prediction literally
and report the taxonomy testing it. Treisman warns her seven binding types may
not share one solution — hence a separate check per error class. The
correct/swapped/guessed decomposition follows Bays, Catalao and Husain (2009).

**Error monitoring.** Detecting an error and changing state without diagnosing
it is motivated by the post-error literature, which does not validate it.
Foerster et al. (2022) tested binding of error-induced control states and found
it weaker and less reliable than stimulus-response binding, the confirmatory
result falling to p = .119 once matched for post-error slowing. Fievez et al.
(2022) found post-error slowing significant only in a hasty context. We cite
these as motivation for a non-introspective design, not evidence it works.

**Structured output.** Fan (2026) separates format effects from prompt-length
confounds across four models and five benchmarks and finds the cost of structure
is **capacity-dependent**: a model with headroom absorbs JSON constraints
(88.7% versus 89.3% on MATH-Hard) while one near its limits degrades sharply
(−28.0pp even with truncation eliminated), the penalty scaling with schema
complexity. That gradient is ours — one field, two fields, integers — and his
result predicts the collapse we measure in a 3B. Our contribution is narrower
and mechanical: we locate *where* the truncation lands, at the escape character,
and give a format which removes it at no capacity cost. His remedy, reason
freely then format, is complementary: both avoid making a small model spend
capacity on syntax.

### References

Bays, P.M., Catalao, R.F.G. & Husain, M. (2009). The precision of visual working
memory is set by allocation of a shared resource. *Journal of Vision* 9(10):7.

Fan, H. (2026). Capacity, not format: rethinking structured reasoning failures.
arXiv:2606.09410.

Fievez, F. et al. (2022). Post-error slowing reflects the joint impact of
adaptive and maladaptive processes. *Frontiers in Human Neuroscience* 16:864590.
doi:10.3389/fnhum.2022.864590

Foerster, A. et al. (2022). Binding error-induced control states. *Journal of
Cognition*. doi:10.5334/joc.213

Markowitz, E. et al. (2026). Google — The Gemma 4 Developer Agent Paper Track.
Kaggle. kaggle.com/competitions/gemma-4-developer-agent-paper

Treisman, A.M. & Gelade, G. (1980). A feature-integration theory of attention.
*Cognitive Psychology* 12(1), 97-136.
