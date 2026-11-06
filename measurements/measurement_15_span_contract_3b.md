# Measurement 15 - the span contract against a 3B, and what it costs

31 October 2026. `run_attenuate.py granite4:3b`, 48 calls, 0 errors, 23.2 min,
median 16.5 s/call. Same seed-0 n=16 question set as every other run.

## Headline: forcing a format destroyed the refusal

| | bare-filename contract (measurement 12) | JSON span contract |
|---|---|---|
| refusals on the false-affirm arm | **16/16** | **2/16** |
| false-affirm rate | **0.000** | **0.875** (14 swaps) |

`granite4:3b` was the project's first local verifier at separation +1.00. Asked
for `{"file", "span"}` under Ollama's schema-constrained decoding, it affirms the
wrong file 14 times out of 16. **The faculty did not survive the contract.**

This was flagged as the risk before the run - "forcing a format forces a
commitment" - and it is now measured. A schema removes the model's cheapest
honest output. `verification: true` in an envelope is therefore a statement
about the contract it was measured under, not about the model.

## Verbatim quotation is a separate capability, and a 3B lacks it

Spans verified on the correct-file arm: **6/16**. The model named the right file
16/16 and could evidence it 6 times.

The 10 failures decompose, and 9 are the model:

| cause | n | example |
|---|---|---|
| returned a fragment, not a span | 5 | `print(f`, `item[`, four spaces |
| did not quote verbatim | 4 | `Windows drive ____ colon` where the source says `letter`; two source lines merged into one |
| my check's whitespace brittleness | 1 | source contains a hard line break mid-word (`unantici\npated`) |

Compare `gemma4:31b` on the identical check: 16/16, zero false rejections.
**False-rejection rate is 0% at 31B and 63% at 3B.** Quoting is gated like
verification is.

## What the span check did buy

Of the 14 swaps it produced, span containment **caught 7 (50%)**. So the check
works as designed - it is the only mechanism in the project that catches swaps,
and swaps are 100% of this project's errors. It simply cannot pay for a 63%
false-rejection rate.

## Attenuation

Verified 10/16, recovered 4 by narrowing, median 3 calls per question.
**Understated:** the run used the pre-H5 build, in which a NONE ended the loop.
The H5 fix (a refusal no longer terminates the search) landed 22 minutes after
the run started and is not reflected here. Re-run before quoting the number.

## Conclusion - the span contract must be envelope-gated

Two new per-model capabilities belong in `calibrate.py`, measured not assumed:

1. **`quotes_verbatim`** - fraction of correct answers whose span verifies.
   31B 1.00, granite4:3b 0.375.
2. **`refusal_survives_schema`** - false-affirm rate under the structured
   contract versus the bare one. 31B unchanged, granite4:3b 0.000 -> 0.875.

Until a model passes both, the engine should use the bare contract with that
model and fall back to existence-only checking - which, per measurement 14,
catches nothing, because no model in this project has ever fabricated.

That is an honest dead end for the fully-offline honest path, and it is a
narrower one than it looks: the 31B passes both at 0.5 s/call.


---

# Part 2 - the fragments are an ESCAPING failure, not a reading failure

31 October 2026. Second arm (`minlen`), 48 calls, 25.9 min. The `minlen` prompt
is identical to `strict` except for four explicit rules: at least one complete
line, at least 30 characters, do not join two lines, do not replace a word with
a placeholder.

## The prompt hypothesis is dead

| | strict | minlen |
|---|---|---|
| named the right file | 16/16 | 16/16 |
| **spans verified** | **6/16** | **6/16** |
| false rejections | 10 | 10 |
| spans under 30 chars (explicitly forbidden) | 6/16 | **6/16** |
| refusals on the wrong file | 2 | 1 |
| swaps caught by span | 7 | 3 |
| median span length | 79 chars | 67 chars |

Eight of the ten failures are **the same questions**, and the fragments are
byte-identical between arms. The model was told "a fragment such as `print(f`
is not acceptable" and returned `print(f`. Telling it the rule changed nothing;
spans got *shorter*.

## What the fragments actually are

All five fragments stop at exactly the same character:

| fragment returned | next character in the source |
|---|---|
| `print(f` | `"` |
| `item[` | `"` |

Five of five. **The model truncates the span at the first character that would
need escaping inside a JSON string.** It is not skimming and it is not failing
to read - it cannot emit `\"` inside a schema-constrained JSON string, so it
stops short. The second failure class is the same problem one layer along: the
"merged lines" span carried a literal `\n` where the source holds a real
newline.

So the 63% false-rejection rate is the ENCODING fighting the contract, not a
reading-capability limit. The earlier conclusion - "verbatim quotation is a
capability a 3B lacks" - is too strong and is withdrawn. What a 3B lacks is the
ability to transcribe text *through a JSON string escape layer*.

## The fix: ask for line numbers, not text

Variant C (`lines`) requests `{"file", "first_line", "last_line"}` over a
line-numbered body. Integers need no escaping. The engine then reads the cited
lines itself and checks that they contain the evidence - the same verification
strength, with no text crossing the model/JSON boundary at all.

`check_lines()` additionally rejects a range outside the file, and a range
longer than 40 lines, because "lines 1-400" is not a citation.

Implemented and self-tested. **Not yet measured** - the arm to run is
`python run_attenuate.py granite4:3b 0 20 lines`.

## What stands regardless

The refusal collapse is unaffected by any of this and remains the harder
problem: 16/16 refusals under the bare contract, 2/16 under the JSON span
contract, 1/16 under `minlen`. Structured output costs this model its ability
to say NONE, and line numbers will not obviously fix that - `{"file": "NONE",
"first_line": 0, "last_line": 0}` is still a schema the model must commit to.
That is the measurement the `lines` arm is really for.
