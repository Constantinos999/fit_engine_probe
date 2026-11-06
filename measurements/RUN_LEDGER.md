# Run ledger - every model run on disk

Rebuilt 2026-11-05 18:07 by `run_ledger.py` from the result
files themselves. It remembers nothing: if a run is not here, its output is
not on disk. **Read this before proposing any run.**

**29 runs · 2186 recorded model calls.**

| when | kind | model | variant | seed | n | calls | s/call | headline |
|---|---|---|---|---|---|---|---|---|
| 2026-10-29 20:19 | raw | `-` | probe_results | - | - | 110 | - | 110 recorded calls |
| 2026-10-30 10:02 | raw | `-` | perobject_gemma4-31b_20261030-095952 | - | - | 264 | - | 264 recorded calls |
| 2026-10-30 10:44 | raw | `-` | perobject_gemma3-1b_20261030-100103 | - | - | 264 | - | 264 recorded calls |
| 2026-10-30 11:41 | raw | `-` | chunked_gemma4-31b_20261030-113954 | - | - | 198 | - | 198 recorded calls |
| 2026-10-30 12:13 | raw | `-` | chunked_gemma3-1b_20261030-114600 | - | - | 198 | - | 198 recorded calls |
| 2026-10-30 12:40 | raw | `-` | calibrate_gemma4-31b_20261030-124006 | - | - | 80 | - | 80 recorded calls |
| 2026-10-30 12:54 | raw | `-` | calibrate_gemma3-1b_20261030-125451 | - | - | 80 | - | 80 recorded calls |
| 2026-10-30 12:59 | raw | `-` | calibrate_gemma4-31b_20261030-125920 | - | - | 112 | - | 112 recorded calls |
| 2026-10-30 13:16 | raw | `-` | calibrate_gemma3-1b_20261030-131659 | - | - | 112 | - | 112 recorded calls |
| 2026-10-30 13:54 | raw | `-` | calibrate_gpt-oss-20b_20261030-135409 | - | - | 112 | - | 112 recorded calls |
| 2026-10-30 13:55 | raw | `-` | screen_gemma4-31b | - | - | 16 | - | 16 recorded calls |
| 2026-10-30 14:24 | raw | `-` | screen_qwen2.5-coder-3b | - | - | 16 | - | 16 recorded calls |
| 2026-10-30 16:41 | raw | `-` | screen_qwen3-1.7b | - | - | 16 | - | 16 recorded calls |
| 2026-10-30 19:45 | raw | `-` | calibrate_qwen3-1.7b_20261030-194503 | - | - | 112 | - | 112 recorded calls |
| 2026-10-30 20:40 | raw | `-` | calibrate_granite4-3b_20261030-204017 | - | - | 112 | - | 112 recorded calls |
| 2026-10-31 10:43 | calibrate | `gemma3:1b` | envelope | 0 | 16 | - | - | separation ?, window None, verifier False |
| 2026-10-31 10:43 | calibrate | `gemma4:31b` | envelope | 0 | 16 | - | - | separation ?, window 3600, verifier True |
| 2026-10-31 10:43 | calibrate | `gpt-oss:20b` | envelope | 0 | 16 | - | - | separation ?, window 3600, verifier True |
| 2026-10-31 10:43 | calibrate | `qwen3:1.7b` | envelope | 0 | 16 | - | - | separation ?, window None, verifier False |
| 2026-10-31 11:49 | calibrate | `granite4:3b` | envelope | 0 | 16 | - | - | separation ?, window 1200, verifier True |
| 2026-10-31 13:16 | attenuate | `granite4:3b` | strict | 0 | 16 | 48 | 16.9 | citation 6/16, swaps 14/16, refused 2 |
| 2026-10-31 13:50 | attenuate | `granite4:3b` | minlen | 0 | 16 | 48 | 18.0 | citation 6/16, swaps 15/16, refused 1 |
| 2026-10-31 15:45 | attenuate | `granite4:3b` | lines | 0 | 16 | - | 16.6 | RESCORED: citation 15/16, swaps caught 16/16, false-affirm 0.0 |
| 2026-10-31 16:40 | attenuate | `granite4:3b` | lines | 0 | 16 | 48 | 17.1 | citation 15/16, swaps 16/16, refused 0 |
| 2026-10-31 16:56 | attenuate | `gemma3:1b` | lines | 0 | 16 | 48 | 10.3 | citation 11/16, swaps 16/16, refused 0 |
| 2026-10-31 16:59 | attenuate | `gemma4:31b` | lines | 0 | 16 | 48 | 2.1 | citation 0/0, swaps 0/0, refused 0 |
| 2026-10-31 17:08 | attenuate | `gpt-oss:20b` | lines | 0 | 16 | 48 | 2.1 | citation 0/0, swaps 0/0, refused 0 |
| 2026-10-31 17:53 | attenuate | `qwen3:1.7b` | lines | 0 | 16 | 48 | 44.4 | citation 6/16, swaps 1/16, refused 2 |
| 2026-10-31 18:18 | attenuate | `qwen2.5-coder:3b` | lines | 0 | 16 | 48 | 15.4 | citation 16/16, swaps 8/16, refused 8 |

## Flagged - do not quote these summaries

- `attenuate_granite4-3b_lines.json` - SUMMARY UNRELIABLE - see D9; use the _rescored file
- `attenuate_gemma3-1b_lines.json` - SUMMARY UNRELIABLE - see D9; use the _rescored file
- `attenuate_gemma4-31b_lines.json` - SUMMARY UNRELIABLE - see D9; use the _rescored file
- `attenuate_gpt-oss-20b_lines.json` - SUMMARY UNRELIABLE - see D9; use the _rescored file
- `attenuate_qwen3-1.7b_lines.json` - SUMMARY UNRELIABLE - see D9; use the _rescored file
- `attenuate_qwen2.5-coder-3b_lines.json` - SUMMARY UNRELIABLE - see D9; use the _rescored file

## Not on disk, therefore not run

Anything absent from the table above. Check here before asking the
user to run something - the cost of a forgotten run is paid twice.
