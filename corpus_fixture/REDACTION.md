# This is a redacted fixture, not the corpus

Every character is replaced by a dot except the text already published verbatim
in `records/` - the evidence tokens and the spans the models quoted. Line
structure is preserved exactly.

It exists so `score_contracts.py` can re-verify every citation without the
original tree being published. Scored against this fixture the contract matrix
is identical, cell for cell, to the same scoring against the real corpus.

It will NOT support anything quoting source text or regenerating the question
set. Scripts needing those refuse when this file is present. Point `FIT_CORPUS`
at a real directory tree to run them.
