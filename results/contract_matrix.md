# Contract x model matrix

Re-scored from raw rows 2026-11-05 18:10. `citation verified` counts rows whose citation passes the engine's own
deterministic check, evidence clause included. `false affirm` is the same
check on the wrong-file arm: a model may name a wrong file freely, it is
counted against it only if a bogus citation would have been BELIEVED.

| model | contract | citation verified | false affirm | separation | errored |
|---|---|---|---|---|---|
| `qwen2.5-coder-3b` | lines | 16/16 | 0/16 | +1.000 | 0 |
| `granite4-3b` | lines | 15/16 | 0/16 | +0.938 | 0 |
| `gemma3-1b` | lines | 11/16 | 0/16 | +0.688 | 0 |
| `qwen3-1.7b` | lines | 6/16 | 0/16 | +0.375 | 0 |
| `granite4-3b` | strict | 4/16 | 0/16 | +0.250 | 0 |
| `granite4-3b` | minlen | 4/16 | 0/16 | +0.250 | 0 |
| `gemma4-31b` | lines **VOID** | 0/0 | 0/0 | +0.000 | 32 |
| `gpt-oss-20b` | lines **VOID** | 0/0 | 0/0 | +0.000 | 32 |
