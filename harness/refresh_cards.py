"""refresh_cards.py - regenerate the derived cards and audit the hand-written one.

The continuity layer is four documents:

  FOUNDATIONS.md   hand-written, changes rarely  - why the project is like this
  START_HERE.md    hand-written, changes weekly  - where the work stands
  RUN_LEDGER.md    DERIVED from result files     - every run ever done
  contract_matrix.md / PAPER_TRAIL.md  DERIVED   - results and traced cases

Derived cards cannot rot: they are rebuilt from disk, so they are correct
whenever they are read. Hand-written cards CAN rot, and a rotted card is worse
than none - it is a superseded number wearing an authoritative face, which is
the project's own failure mode (748,003 still sits in five Armadillo files).

So this script does two things:
  1. rebuilds every derived card
  2. AUDITS START_HERE.md against the rebuilt data and reports any figure it
     quotes that no longer matches, rather than silently correcting it

Run it at session close, or any time. Model-free, offline, safe to repeat.
usage:  python refresh_cards.py
"""
import os, re, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
DERIVED = ["run_ledger.py", "score_contracts.py", "paper_trail.py"]


def run(script):
    p = os.path.join(HERE, script)
    if not os.path.exists(p):
        return script, "MISSING", ""
    r = subprocess.run([sys.executable, p], capture_output=True, text=True, cwd=HERE)
    tail = (r.stdout or r.stderr or "").strip().splitlines()
    return script, ("ok" if r.returncode == 0 else f"FAILED rc={r.returncode}"), \
        (tail[0] if tail else "")


def audit_start_here():
    """Check the numbers START_HERE.md quotes against the rebuilt matrix."""
    sh = os.path.join(CANONICAL, "START_HERE.md")   # the copy a person edits (D10)
    mx = os.path.join(HERE, "contract_matrix.json")
    if not (os.path.exists(sh) and os.path.exists(mx)):
        return ["START_HERE.md or contract_matrix.json missing - cannot audit"]
    # NAME FORMS: envelopes and filenames use `gemma4-31b`, prose uses
    # `gemma4:31b`. Comparing the two raw forms is the same defect class as D9
    # (token/tok) and it has now appeared three times in this project, so the
    # comparison is normalised rather than trusted.
    def norm(x):
        return re.sub(r"[^a-z0-9]", "", str(x).lower())
    text = open(sh, encoding="utf-8").read()
    ntext = norm(text)
    rows = json.load(open(mx, encoding="utf-8"))
    live = {}
    for r in rows:
        if r.get("void"):
            continue
        live[(r["model"], r["variant"])] = (r["hit"]["citation_verified"],
                                            r["hit"]["n"],
                                            r["fa"]["citation_verified"],
                                            r["separation"])
    notes = []
    for (model, variant), (cv, n, fa, sep) in sorted(live.items()):
        if variant != "lines":
            continue
        pat = rf"{re.escape(str(cv))}\s*/\s*{re.escape(str(n))}"
        if norm(model) in ntext:
            if not re.search(pat, text):
                notes.append(f"{model} ({variant}): matrix says citation "
                             f"{cv}/{n}, separation {sep:+.3f} - not found in "
                             f"START_HERE.md; check that card")
        else:
            notes.append(f"{model} ({variant}) is in the matrix "
                         f"({cv}/{n}, {sep:+.3f}) but START_HERE.md does not "
                         f"mention it at all")
    # void runs must be named somewhere, or someone will quote their zero
    for r in rows:
        if r.get("void") and norm(r["model"]) not in ntext:
            notes.append(f"{r['model']} ({r['variant']}) is VOID with "
                         f"{r.get('errors')} errored calls and is not flagged "
                         f"in START_HERE.md - a reader may quote its zero")
    return notes



# ------------------------------------------------- one canonical destination ---
# Driving files live at the tracker ROOT; per-session logs live in the numbered
# subfolders. A derived card copied into several folders becomes several cards
# with several dates, and a later session must guess which is current. That is this project's
# own failure mode (748,003 sits in five Armadillo files and is wrong in all of
# them). So the cards have ONE home and this script writes it.
CANONICAL = os.environ.get("FIT_TRACKER",
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "measurements"))
# DERIVED cards only. START_HERE.md and FOUNDATIONS.md are hand-written and live
# at CANONICAL as the single copy - publishing them from HERE gave them a second
# home and silently reverted every correction made at the root (defect D10).
CARDS = ["RUN_LEDGER.md", "contract_matrix.md", "PAPER_TRAIL.md"]


def publish():
    import shutil
    if not os.path.isdir(CANONICAL):
        print(f"  [skip] {CANONICAL} not present")
        return
    for c in CARDS:
        src = os.path.join(HERE, c)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(CANONICAL, c))
            print(f"  published  {c}")



def archive(session_folder):
    """Copy the current START_HERE.md into a session folder, stamped SUPERSEDED.

    The current card is identified by PATH - always CANONICAL/START_HERE.md.
    Archived copies are history and are headed so nobody quotes one as current.
    Skipping this step costs a snapshot, never the thread.
    """
    import datetime
    src_card = os.path.join(CANONICAL, "START_HERE.md")
    dest_dir = os.path.join(CANONICAL, session_folder)
    if not os.path.exists(src_card):
        print(f"  [skip] {src_card} not present"); return
    if not os.path.isdir(dest_dir):
        print(f"  [skip] {dest_dir} is not a folder - create it first")
        return
    stamp = datetime.date.today().isoformat()
    out = os.path.join(dest_dir, f"START_HERE_SUPERSEDED_{stamp}.md")
    head = (f"> **SUPERSEDED {stamp}.** The state card as it stood at the close of this\n"
            f"> session. The current card is always `START_HERE.md` at the tracker root.\n"
            f"> Nothing below should be quoted as current.\n\n")
    with open(src_card, encoding="utf-8") as f: body = f.read()
    with open(out, "w", encoding="utf-8") as f: f.write(head + body)
    print(f"  archived   {os.path.relpath(out, CANONICAL)}")


def main():
    import sys
    if "--archive" in sys.argv:
        print("== archiving the outgoing state card ==")
        archive(sys.argv[sys.argv.index("--archive") + 1])
        print()
    print("== rebuilding derived cards ==")
    for s in DERIVED:
        name, status, first = run(s)
        print(f"  {name:<22} {status:<12} {first}")
    print("\n== publishing to the canonical folder ==")
    publish()
    print("\n== auditing START_HERE.md against the rebuilt data ==")
    notes = audit_start_here()
    if not notes:
        print("  no discrepancies found")
    else:
        for n in notes:
            print(f"  STALE?  {n}")
    print("\nDerived cards are rebuilt. START_HERE.md and FOUNDATIONS.md are")
    print("hand-written: fix them yourself, deliberately. This script will not")
    print("edit a card a human wrote - a silent correction reads to a later")
    print("session as if the file had always been right.")


if __name__ == "__main__":
    main()
