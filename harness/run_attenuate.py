"""
run_attenuate.py - does a local model hold the span contract, and does attenuation
                   recover what a too-wide window loses?

    python run_attenuate.py granite4:3b            # 48 calls
    python run_attenuate.py qwen3:1.7b 0 20

Three arms per question, all on ONE file at a time:

  hit    the file that DOES contain the evidence, at the model's calibrated
         window -> contract compliance, and the span check's FALSE-REJECTION rate
  fa     a file that does NOT -> does it refuse? and if it swaps instead, does the
         span check catch it? THIS IS THE UNTESTED CLAIM: gemma4:31b refused 16/16
         so it produced no swaps to catch.
  atten  the correct file at 3,600 chars - above granite4:3b's calibrated cap of
         1,200, where it fabricated memory_inject.md - with the attenuation loop
         running. Does halving the window recover the answer?

Writes attenuate_<model>.jsonl (one row per call, flushed, with per-call seconds -
harness defect H6 was calibrate.py recording no timings) and attenuate_<model>.json.
"""
import json
import os
import random
import sys
import time
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import attenuate as at
import heldout as ho

URL = "http://localhost:11434/api/generate"
MODEL = sys.argv[1] if len(sys.argv) > 1 else "granite4:3b"
VARIANT = sys.argv[4] if len(sys.argv) > 4 else "strict"
SEED = int(sys.argv[2]) if len(sys.argv) > 2 else 0
NQ = int(sys.argv[3]) if len(sys.argv) > 3 else 20
HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
RECORDS = os.environ.get("FIT_RECORDS", os.path.join(PKG, "records"))
RESULTS = os.environ.get("FIT_RESULTS", os.path.join(PKG, "results"))
MEASUREMENTS = os.environ.get("FIT_MEASUREMENTS", os.path.join(PKG, "measurements"))
CORPUS = os.environ.get("FIT_CORPUS") or next(
    (p for p in (os.path.join(PKG, "replica"),
                 os.path.join(PKG, "corpus_fixture")) if os.path.isdir(p)),
    os.path.join(PKG, "corpus_fixture"))

env_path = os.path.join(RESULTS, f"envelope_{MODEL.replace(':', '-')}.json")
WINDOW = 1200
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as fh:
        WINDOW = json.load(fh)["recommend"].get("max_bytes_per_object") or 1200
WIDE = 3600


def ask(prompt, timeout=300):
    body = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                       "format": (at.SCHEMA_LINES if VARIANT == "lines" else at.SCHEMA),
                       "options": {"temperature": 0, "num_predict": 400}}).encode()
    req = urllib.request.Request(URL, data=body,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode()).get("response", "")


def main():
    corpus = ho.read_corpus()
    qs = ho.generate(NQ, SEED, corpus=corpus)
    rnd = random.Random(13)
    tag = MODEL.replace(':', '-') + ("" if VARIANT == "strict" else "_" + VARIANT)
    raw_path = os.path.join(RECORDS, f"attenuate_{tag}.jsonl")
    # Every run keeps its own record. The canonical name is what the scorers
    # read; a timestamped copy of any PREVIOUS run is preserved first so a
    # re-run can never destroy a result that cost half an hour of model calls.
    stamp = time.strftime("%Y%m%d-%H%M%S")
    for prev in (raw_path, os.path.join(RECORDS, f"attenuate_{tag}.json")):
        if os.path.exists(prev):
            import shutil as _sh
            _sh.copy2(prev, prev.replace(".json", f"_{stamp}.bak.json"))
            print(f"[guard] previous result preserved -> "
                  f"{os.path.basename(prev).replace('.json', f'_{stamp}.bak.json')}")
    rows = []
    fh = open(raw_path, "w", encoding="utf-8")

    def record(**r):
        rows.append(r)
        fh.write(json.dumps(r) + "\n")
        fh.flush()

    print(f"[*] {MODEL} ({VARIANT}) - {len(qs)} questions x 3 arms = {len(qs) * 3} calls")
    print(f"[*] calibrated window {WINDOW}, wide window {WIDE}")
    t0 = time.time()
    for i, q in enumerate(qs, 1):
        home, off = q["home"][0], q.get("offset", 0)
        wrong = rnd.choice([k for k in corpus if k != home])

        for arm, fname, text, offset, window in (
                ("hit", home, corpus[home], off, WINDOW),
                ("fa", wrong, corpus[wrong], 0, WINDOW)):
            t = time.time()
            try:
                raw, err = ask(at.build_prompt(q["q"], fname, text, window, offset, VARIANT)), None
            except Exception as e:
                raw, err = "", f"{type(e).__name__}: {e}"
            secs = round(time.time() - t, 1)
            if VARIANT == "lines":
                f, lo, hi = at.parse_lines(raw)
                sp = f"{lo}-{hi}"
                ex_ok, ex_why = at.check_existence(f, corpus)
                # D9 (found 31 Oct): this read q.get("token") but heldout.generate
                # emits the key "tok". get() returned None on every question, so
                # check_lines skipped its evidence clause and scored a citation as
                # verified whenever the line RANGE was valid - which it always is.
                # The first lines-contract run therefore reported hit 16/16 and
                # false-affirm 16/16; re-scored with the evidence check actually
                # running, the same raw output is hit 15/16 and false-affirm 0/16.
                sp_ok, sp_why = at.check_lines(f, lo, hi, corpus,
                                               evidence=q.get("tok"))
            else:
                f, sp = at.parse(raw)
                ex_ok, ex_why = at.check_existence(f, corpus)
                sp_ok, sp_why = at.check_span(f, sp, corpus)
            right = (f or "").lower().lstrip(".") == home.lower().lstrip(".")
            record(arm=arm, qid=q["id"], shown=fname, window=window, file=f,
                   span=(sp or "")[:200], named_right=right, refused=(f or "").upper() == "NONE",
                   exists=ex_ok, span_ok=sp_ok, why=sp_why, secs=secs, error=err,
                   raw=str(raw)[:300])
            print(f"  [{len(rows):>3}/{len(qs)*3}] {arm:<5} {q['id']:<8} -> {str(f)[:22]:<22} "
                  f"span={'ok' if sp_ok else sp_why[:22]:<24} {secs:>5}s")

        # attenuation: start ABOVE the calibrated cap and let the loop find the window
        t = time.time()
        calls = {"n": 0}

        def counting_ask(prompt):
            calls["n"] += 1
            try:
                return ask(prompt)
            except Exception as e:
                return f'{{"file":"ERROR","span":"{type(e).__name__}"}}'

        res = at.attenuate(counting_ask, q["q"], home, corpus[home], corpus,
                           window=WIDE, offset=off, variant=VARIANT)
        secs = round(time.time() - t, 1)
        record(arm="atten", qid=q["id"], shown=home, window=res["window"],
               file=res["answer"], span=(res.get("span") or "")[:200],
               named_right=(res["answer"] or "").lower().lstrip(".") == home.lower().lstrip("."),
               refused=res["answer"] == at.NONE, exists=None, span_ok=res["verified"],
               why=f"attenuated {res['attenuated']} step(s)", secs=secs, error=None,
               calls=calls["n"], trail=res["trail"])
        print(f"  [{len(rows):>3}/{len(qs)*3}] atten {q['id']:<8} -> {str(res['answer'])[:22]:<22} "
              f"window {WIDE}->{res['window']} in {calls['n']} call(s)  {secs:>5}s")
    fh.close()

    def arm(a):
        return [r for r in rows if r["arm"] == a and not r.get("error")]

    hit, fa, atn = arm("hit"), arm("fa"), arm("atten")
    fr = [r for r in hit if r["named_right"] and not r["span_ok"]]
    swaps = [r for r in fa if not r["refused"] and r["file"] not in (None, "ERROR")]
    caught = [r for r in swaps if not r["span_ok"]]
    summary = dict(
        model=MODEL, seed=SEED, n_questions=len(qs), window=WINDOW, wide=WIDE,
        prompt_variant=VARIANT,
        contract=dict(parseable=sum(1 for r in hit if r["file"]), n=len(hit)),
        hit=dict(named_right=sum(r["named_right"] for r in hit),
                 span_verified=sum(r["span_ok"] for r in hit), n=len(hit),
                 false_rejection=len(fr)),
        fa=dict(refused=sum(r["refused"] for r in fa), swaps=len(swaps),
                swaps_caught_by_span=len(caught), n=len(fa)),
        attenuation=dict(verified=sum(r["span_ok"] for r in atn), n=len(atn),
                         recovered=sum(1 for r in atn if r["span_ok"] and r["window"] < WIDE),
                         median_calls=sorted(r.get("calls", 1) for r in atn)[len(atn) // 2] if atn else 0),
        median_secs=sorted(r["secs"] for r in rows if r.get("secs"))[len(rows) // 2],
        errors=sum(1 for r in rows if r.get("error")),
        elapsed_min=round((time.time() - t0) / 60, 1))
    out = os.path.join(RECORDS, f"attenuate_{tag}.json")
    with open(out, "w", encoding="utf-8") as f2:
        json.dump(summary, f2, indent=1)
    print("\n================ SUMMARY ================")
    print(json.dumps(summary, indent=1))
    print(f"\n[*] summary -> {out}\n[*] raw rows -> {raw_path}")


if __name__ == "__main__":
    main()
