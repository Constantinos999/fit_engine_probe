# Measurement 13 - dynamic attenuation, and the span contract

31 October 2026. `attenuate.py`, 19/19 self-test, plus 32 calls to `gemma4:31b`.

## What it is

The engine stops being told a window and finds one. It starts from the
calibrated `max_bytes_per_object`, asks, runs a check with NO MODEL IN IT, and
halves the window until the check passes or it refuses. An unknown model dropped
in cold converges to its own working window instead of being trusted at someone
else's.

Trigger, in order:

| check | catches | why it is needed |
|---|---|---|
| EXISTENCE - is the named file in the corpus? | fabrication | `granite4:3b` invents `memory_inject.md` at 3,600 chars and never at 400 or 1,200, so an existence failure IS a signal that the window is too wide |
| SPAN - does the quoted evidence occur verbatim in the named file? | swaps | all 16 routing errors in measurement 8 named a real file, just the wrong one; existence would have caught none of them |

Answer contract: `{"file": ..., "span": "<copied verbatim>"}`, with
`{"file": "NONE", "span": ""}` as a first-class honest answer.

## Two defects found by the module's own self-test, before any model ran

**1. A shrinking prefix window deletes the evidence.** The first loop truncated
from the start, so attenuating moved the evidence out of view and the model
correctly answered NONE - the loop would have destroyed recall while appearing to
work. Windows are now CENTRED on the candidate offset the deterministic ranker
already knows. Two controls assert it: a 400-char centred window keeps the
evidence, the same prefix window loses it.

**2. Escaping, worth 6% of all correct answers.** Measured on 16 hit-arm calls:
`gemma4:31b` named the right file 16/16, and the span check rejected one of them.
The span was `print(f"\n[Error] Failed to connect to Ollama server: {e}")` from a
`.py` file. The file stores two characters - backslash, n - and the model's JSON
decoded `\n` into a real newline. **A 6% false-rejection rate created entirely by
escaping, not by the model.** The check now tries both readings, which is
arithmetic rather than judgement. Re-scored offline from the saved run: 16/16,
zero false rejections, and a control asserts a genuinely wrong span is still
rejected.

## Result

| arm | n | outcome |
|---|---|---|
| correct file shown | 16 | named right 16/16; span verified **16/16** after the escaping fix (15/16 before) |
| wrong file shown | 16 | refused with NONE **16/16** |

## What is NOT established

**The swap-catch rate is untested.** `gemma4:31b` refused correctly on all 16
false-affirm calls, so it produced no swaps for the span check to catch. The
claim that span containment catches swaps is still an argument, not a
measurement. It needs a model that actually swaps - `granite4:3b` at 3,600 chars,
or `qwen3:1.7b`, both of which must run on the user's machine.

Also untested: whether a smaller model can follow the JSON span contract at all.
Local Ollama enforces schema-constrained decoding, which should help, but forcing
a format forces a commitment - the open question is whether refusals survive or
get converted into swaps.


## Addendum — withheld

The original addendum recorded how attenuation was wired into the engine:
the opt-in flag and its default, what the receipt carries, the refusal
handling in the narrowing loop, and an end-to-end run through the engine.
That is implementation detail of the FIT Engine, which is not part of this
release, so it is withheld here. Nothing in the measurement above depends
on it: the attenuation result stands on `attenuate.py` and the saved runs,
both of which are included.
