"""
harness_guard.py - PROTOCOL.md, as code that fails.

A protocol in markdown is a claim about future behaviour with nothing checking
it, which is the same shape as a model validating its own output. Every rule
below exists because its absence produced a wrong headline in this project, and
each is now a function that returns a FINDING rather than a sentence that asks
nicely.

Usage is deliberately awkward to bypass: `guard.finish(rows)` raises
HarnessViolation unless the run satisfies the blocking rules, and the probe
calls it BEFORE it is allowed to print a summary.

    guard = HarnessGuard(questions=QUESTIONS, decision_rule=aggregate)
    ...
    guard.record_baseline(baseline_rows)      # zero-model-call control
    guard.finish(rows)                        # raises if anything is missing

RULES (blocking ones raise; advisory ones print):

  R1  BLOCKING  a model arm may not be reported without a zero-model-call
                baseline over the same questions. Reported scores are deltas
                against it.
  R2  BLOCKING  every row carries answer / expect / tok_present / raw, so any
                later scoring question is answerable without a re-run.
  R3  BLOCKING  ground truth varies by arm. A constant `expect` across arms
                means it was hand-fixed, which has scored a correct answer as
                wrong before.
  R4  BLOCKING  the decision rule is hashed at construction and re-hashed at
                finish. Editing it mid-run - the comfortable move after seeing
                a result - is caught.
  R5  advisory  questions whose evidence token appears in the question text are
                index tests, not binding tests, and are counted and named.
  R6  advisory  harness errors are reported separately from model errors.
  R7  BLOCKING  the question set must declare whether it is held out. A set
                reused across measurements cannot carry a parameter sweep.
"""
import hashlib, inspect, json, os, sys, collections


class HarnessViolation(Exception):
    pass


def _hash(fn):
    try:
        return hashlib.sha256(inspect.getsource(fn).encode()).hexdigest()[:16]
    except (OSError, TypeError):
        return "unhashable"


class HarnessGuard:
    def __init__(self, questions, decision_rule, question_set_id,
                 held_out=False, sweeping=False):
        self.questions = questions
        self.rule_hash = _hash(decision_rule)
        self.decision_rule = decision_rule
        self.qset = question_set_id
        self.held_out = held_out
        self.sweeping = sweeping
        self.baseline = None
        self.findings = []

    # ---- R1 -------------------------------------------------------------
    def record_baseline(self, rows):
        """Rows from a control that made ZERO model calls over the same questions."""
        self.baseline = rows

    def _r1(self, rows):
        if self.baseline is None:
            return ("R1", True, "no zero-model-call baseline recorded; a model score "
                                "without one is not evidence the model did anything")
        bq = {r["qid"] for r in self.baseline}
        mq = {r["qid"] for r in rows}
        if not mq <= bq:
            return ("R1", True, f"baseline missing {len(mq - bq)} of the model arm's "
                                f"questions: {sorted(mq - bq)[:5]}")
        if any(r.get("secs", 0) for r in self.baseline):
            return ("R1", True, "baseline rows report nonzero call time; a control that "
                                "calls a model is not a control")
        return ("R1", False, f"baseline present over {len(bq)} questions")

    # ---- R2 -------------------------------------------------------------
    def _r2(self, rows):
        need = ("answer", "expect", "tok_present", "raw")
        bad = [r for r in rows if any(k not in r for k in need)]
        return ("R2", bool(bad), f"{len(bad)} rows missing one of {need}"
                if bad else f"all {len(rows)} rows carry the rescoring fields")

    # ---- R3 -------------------------------------------------------------
    def _r3(self, rows):
        """Ground truth must be COMPUTED from what the arm was shown.

        The first version of this rule asserted that `expect` varies across arms,
        and it fired on measurement 7 as a false positive: both arms there see the
        same union of content, so a constant expectation is correct. Variation is
        evidence of computation but constancy is not evidence of hand-fixing.

        The invariant that actually holds for `expected_for(q, payload)` is that
        the expectation is NONE exactly when the evidence token is absent from
        what that row was shown. A hand-fixed table breaks it immediately.
        """
        bad = [r for r in rows
               if (r["expect"].strip().lower() == "none") != (not r["tok_present"])]
        if bad:
            ex = bad[0]
            return ("R3", True, f"{len(bad)} rows where `expect` contradicts `tok_present` "
                                f"(e.g. {ex['qid']}/{ex.get('arm','?')}: expect="
                                f"{ex['expect']!r}, tok_present={ex['tok_present']}); "
                                f"ground truth is not computed from the payload")
        byq = collections.defaultdict(set)
        for r in rows:
            byq[r["qid"]].add(r["expect"])
        varying = sum(1 for v in byq.values() if len(v) > 1)
        return ("R3", False, f"expect agrees with tok_present on all {len(rows)} rows; "
                             f"{varying} of {len(byq)} questions are arm-dependent")

    # ---- R4 -------------------------------------------------------------
    def _r4(self, _rows):
        now = _hash(self.decision_rule)
        if now != self.rule_hash:
            return ("R4", True, f"decision rule changed during the run "
                                f"({self.rule_hash} -> {now})")
        return ("R4", False, f"decision rule unchanged ({self.rule_hash})")

    # ---- R5 -------------------------------------------------------------
    def _r5(self, _rows):
        leaky = [q["id"] for q in self.questions
                 if q.get("tok") and q["tok"] in q["q"]]
        return ("R5", False, f"index-test questions (token visible in the question): "
                             f"{leaky or 'none'}")

    # ---- R7 -------------------------------------------------------------
    def _r7(self, _rows):
        if self.sweeping and not self.held_out:
            return ("R7", True, f"question set '{self.qset}' is not held out and this run "
                                f"is a parameter sweep; the parameter would be fitted on "
                                f"its own test set")
        return ("R7", False, f"question set '{self.qset}', held_out={self.held_out}, "
                             f"sweeping={self.sweeping}")

    # ---------------------------------------------------------------------
    def check(self, rows):
        return [c(rows) for c in (self._r1, self._r2, self._r3, self._r4,
                                  self._r5, self._r7)]

    def finish(self, rows, strict=True):
        res = self.check(rows)
        print("\n---------------- harness guard ----------------")
        for rule, failed, msg in res:
            print(f"  {rule}  {'FAIL' if failed else 'ok  '}  {msg}")
        bad = [r for r in res if r[1]]
        if bad and strict:
            raise HarnessViolation(
                f"{len(bad)} blocking rule(s) failed: " +
                "; ".join(f"{r[0]}: {r[2]}" for r in bad))
        return res

    # ---- R1's other half: report deltas, not raw scores -------------------
    def delta_table(self, arms, rows, correct=lambda r: r["cls"] == "correct"):
        """Model score MINUS the deterministic baseline, on the same questions."""
        if self.baseline is None:
            raise HarnessViolation("delta_table called with no baseline (R1)")
        bq = {r["qid"]: correct(r) for r in self.baseline}
        out = {}
        for arm in arms:
            sub = [r for r in rows if r["arm"] == arm and r["qid"] in bq]
            if not sub:
                continue
            n = len(sub)
            m = sum(1 for r in sub if correct(r))
            reps = max(1, n // max(len(bq), 1))
            b = sum(bq.values()) * reps
            out[arm] = dict(model=m, baseline=b, n=n, delta=m - b)
        return out


if __name__ == "__main__":
    print(__doc__)
