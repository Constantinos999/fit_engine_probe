# Literature cross-check — what a search found, and what it did not

31 October 2026. Two web searches after measuring the span-contract collapse.

## A correction, first

An earlier draft of this file quoted specific figures — benchmark deltas, an
IFEval score, a model's average rank. **Those numbers could not be verified
against the retrieved results and have been removed.** The persisted search
output contains titles and URLs only, with no body text, so nothing quantitative
from it can be read back. Writing unverifiable numbers into a document whose
purpose was independent verification is this project's own failure mode, and it
is recorded here rather than quietly fixed.

What follows is restricted to what the result list itself supports: that a
literature exists, what it is called, and what its titles claim.

## 1. The phenomenon we measured has a literature

Search: *structured output JSON mode degrades LLM reasoning performance*.
Nine results, of which five are directly on point:

| source | what the title asserts |
|---|---|
| **The Structured Output Benchmark** (arXiv 2604.25359) | structured output *quality* is a distinct thing, benchmarked across multiple sources |
| **Capacity, Not Format: Rethinking Structured Reasoning Failures** (arXiv 2606.09410) | **argues the failures are about model capacity, not the format** |
| **Prompt Complexity Dilutes Structured Reasoning** (arXiv 2603.13351) | prompt complexity degrades structured reasoning |
| *Your JSON Is Valid but Your Data Is Wrong: Five Failure Modes Structured Outputs Won't Catch* | schema validity does not imply correctness |
| *Structured Outputs Are Not a Solved Problem: JSON Mode Failure Modes in Production* | the failure modes are known and unresolved in practice |

So the question is active and the failure is recognised. Note the second entry
especially: **its title argues against the framing I was reaching for.** If
structured-reasoning failures are capacity rather than format, then granite's
collapse may be a small-model limitation that the schema exposes rather than
causes — which is a different claim from "the schema destroyed it", and our own
data cannot presently separate them. We measured one model under two contracts;
we did not measure a large model under the same two contracts on the same
questions. **That control is missing and is cheap: gemma4:31b, bare contract
versus span contract, 32 calls.**

The fourth title is the sharpest fit to what we actually observed — valid JSON,
wrong data. Granite's 14 swaps were all schema-perfect.

## 2. The models

Search: *Granite 4.0 3B Qwen3 1.7B small model instruction following benchmark
comparison*. Relevant results exist and are named here as leads, with no figures
quoted:

- a GitHub benchmark of **IBM Granite 4.1 8B vs Llama 3.1, Qwen 2.5, Mistral 7B**
  on tool calling and instruction following
- **"We Benchmarked 12 Small Language Models Across 8 Tasks"** (distillabs)
- **"LFM3-1.7B-Base vs Granite 4.2 3B: Trunk or Reasoner?"** (orcarouter)
- IBM's own Granite documentation and the 4.0 / 4.1 model cards

A caveat that applies to all of them regardless of their contents: these cover
Granite 4.0, 4.1 and 4.2 across dense, hybrid and MoE architectures at several
sizes. `granite4:3b` as pulled through Ollama is not necessarily the checkpoint
any given table describes, and vendor benchmark numbers are self-reported.

## 3. What this exercise is worth

It establishes that the phenomenon is known and gives us the vocabulary and the
sources to read properly. It does **not** yet give us an independent number to
compare ours against, because the retrieved results were not read in full.

To do this properly the next step is to fetch the two arXiv papers by DOI and
read them, rather than searching again. Both are reachable.

## 4. The control this search identified, which matters more than the citations

**Run the bare-versus-span comparison on gemma4:31b, same questions, 32 calls.**
If the 31B also loses refusals under the schema, the cause is the contract and
our fix (line numbers, or decoupled two-pass formatting) is the right one. If
the 31B is unaffected, the cause is capacity, granite is simply below the floor
for structured honesty, and no contract change will rescue it.

We have asserted the first and not tested it. The paper title in section 1 is a
direct warning that the second is live.

## 5. Resolved — the Fan paper was fetched and read

7 November 2026. arXiv:2606.09410 was retrieved from the arXiv API and its
abstract read directly: Hengxin Fan, published 8 June 2026, *Capacity, Not
Format: Rethinking Structured Reasoning Failures*. Every figure cited in the
paper's section 11 appears verbatim in the abstract — Sonnet 88.7±4.0% JSON
against 89.3±1.7% CoT on MATH-Hard, GPT-4o-mini −28.0pp with extended budgets
eliminating truncation, four models across five benchmarks, the penalty scaling
with schema complexity (McNemar p < 0.0001), and the delayed-structure remedy,
reason freely then format. The citation is safe to quote.

Section 1 above still warns these numbers could not be verified. It was correct
when written and is now superseded. The warning is left in place rather than
deleted, because a file corrected in silence reads to a later session as if it
had always been right — but note the cost: two separate sessions have re-fetched
this paper after reading section 1 and raising a false alarm.
