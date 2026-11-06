# Measurement 16 - the escaping-free contract, and two defects in the scorer

**Model** `granite4:3b` (local, Ollama) · **run** 31 Oct 2026, 48 calls, 0 errors,
28 min, median 16.6 s/call · **questions** the frozen 16 from `heldout.generate(20, 0)`
· **raw** `attenuate_granite4-3b_lines.jsonl`

## What was being tested

Measurement 15 found that `granite4:3b` verified a citation 6/16 under the JSON
`{file, span}` contract, and that all five inspected fragments stopped at exactly
the character requiring JSON escaping - in 5 of 5 cases the next source character
was a double quote. The hypothesis: the model cannot emit `\"` inside a
schema-constrained string, so it truncates.

`PROMPT_LINES` removes the boundary entirely. The body is shown line-numbered and
the model returns `{file, first_line, last_line}` - integers, which need no
escaping. **No text crosses the model/JSON boundary at all.** The engine then
reads the cited lines itself.

## The two defects

The run's own summary reported hit 16/16 and false-affirm 16/16, which reads as a
verifier with no teeth: a line range always exists, so the check always passes.
That reading was wrong, and so was the summary.

**D8 - the attenuation loop ignored its own variant argument.** `attenuate()`
accepted `variant=` and passed it to `build_prompt`, then called `parse()` and
`check_span()` whatever the variant. The lines contract returns no text span, so
every check failed, the window halved to the floor, and all 16 questions returned
NONE. The reported `attenuation: verified 0/16` was a wiring defect, not a result.
Fixed, with three regression tests (`D8-lines-verifies`,
`D8-lines-out-of-range-refuses`, `D8-lines-unknown-file-refuses`).

**D9 - a key-name mismatch silently disabled the evidence check.** The scorer
called `check_lines(..., evidence=q.get("token"))`. `heldout.generate` emits the
key **`tok`**. `get()` returned `None` on all 16 questions, and `check_lines`
skips its evidence clause when `evidence` is falsy:

```python
if evidence and evidence not in "\n".join(lines[lo - 1:hi]):
    return False, "cited lines do not contain the evidence"
```

So a citation was scored verified whenever the line *range* was valid - which it
always is. This is the defect that matters: it does not crash, it does not warn,
and it inflates the headline in the flattering direction. It would have gone into
the paper as a triumph.

## Re-scored

The raw replies were re-scored offline with the evidence clause supplied. **No new
model calls** - same 48 replies, correct arithmetic.

| arm | result |
|---|---|
| hit - named the right file | 16/16 |
| hit - citation verified *with evidence* | **15/16** |
| fa - named a wrong file (swap) | 16/16 |
| fa - refused | 0/16 |
| fa - swap caught by the citation check | **16/16** |
| effective false-affirm rate | **0.000** |
| separation | **+0.94** |

Against the text-span contract on the same questions: citation verified 6/16 by
that run's own check, 4/16 under the stricter standard `score_contracts.py` now
applies uniformly; swaps caught 7/16; false-affirm 0.875.

The single rejection is the check working, not failing. On `g0_10` the model named
`subsystem_daemon.py` - correct - and cited line 69. The token `Synchronized` is at
line 62. A right file with a wrong line is exactly the error a bare-filename
contract cannot see and would have scored as a win.

## What it means

The escaping hypothesis is confirmed: remove the need to escape and a 3B model's
verified-citation rate goes from 4-6 of 16 to 15 of 16, on identical questions at
temperature 0.

The refusal collapse persists and is now the sharper finding. Refusals under the
three contracts: bare 16/16, span 2/16, lines 0/16. This was predicted in writing
before the run - the lines contract was expected not to fix it, because
`{file: NONE, first_line: 0, last_line: 0}` is still a commitment the schema
demands. Note what the bare contract is *not*: it is not schema-free. It
constrains the reply to `{"answer": "<filename>"}` - **one** field. The span and
lines contracts add a **second** field the model must fill. That is the only
difference between them, so that is what the refusal collapse is attributable to:
not schema constraint, but being required to produce a citation alongside the
answer. Asked for an answer, the model will say it does not know; asked for an
answer *and* a citation, it prefers a coherent wrong pair to an incoherent refusal.

**And it does not matter.** The engine's false-affirm rate is 0.000 under the
lines contract despite the model refusing zero times out of sixteen, because every
one of the sixteen swaps produced a citation that failed a deterministic check.
The model was never honest; it was *checkable*. That is the architectural claim
this project exists to test, and this is the measurement that supports it: do not
ask a small model to know what it does not know - ask it for a citation an
ordinary function can verify, and refuse on its behalf.

## Open

- The attenuation arm is void until R1 in `RUNBOOK.md` is re-run with D8 fixed.
- Measured on one model. The contract x model matrix (R2) is unrun, and with it
  the capacity-versus-format control the literature asks for.
