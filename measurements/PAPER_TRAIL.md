# Paper trail - 18 real cases, traced by hand

Generated 2026-11-10 18:21 by `paper_trail.py` from saved
raw rows. No model was called. Every case can be checked against the
repository without running anything: the question, the model's answer, the
engine's deterministic verdict, and the evidence's true location on disk.

This is item 4 on the blueprint (the grey GATE box) and DeepSeek's
prescription: trace real cases before trusting a database built over them.
It was skipped once, and D9 - an evidence check disabled by a key-name
mismatch, invisible to every automated probe - is what that cost.

---

## Case 1 - RIGHT FILE, BAD CITATION  <-- caught only by the span check

- **question** (g0_10, lines contract, `hit` arm): Which file contains a line reading `print(f"[*] [Daemon ____] Updated payload -> {PAYLOAD_PATH}")` , where ____ is a single identifier?
- **evidence token**: `Synchronized`
- **file shown to the model**: `subsystem_daemon.py`  ·  **home file**: `subsystem_daemon.py`
- **model answered**: `subsystem_daemon.py`  span `69-69`
- **what those lines actually say**: `........ . ....`
- **engine check**: FAIL - cited lines do not contain the evidence
- **the token really lives at**: `subsystem_daemon.py`:62 -> `print(f"[*] [Daemon Synchronized] Updated payload -> {PAYLOAD_PATH}")`

## Case 2 - RIGHT FILE, BAD CITATION  <-- caught only by the span check

- **question** (g0_00, strict contract, `hit` arm): Which file contains a line reading `print(f"\n[Error] ____ to connect to Ollama server: {e}")` , where ____ is a single identifier?
- **evidence token**: `Failed`
- **file shown to the model**: `local_runner.py`  ·  **home file**: `local_runner.py`
- **model answered**: `local_runner.py`  span `print(f\n[Error] Failed to connect to Ollama server: {e}\n[!] Ensure the Ollama background service is running.)`
- **what those lines actually say**: `print(f\n[Error] Failed to connect to Ollama server: {e}\n[!] Ensure the Ollama background service is running.)`
- **engine check**: FAIL - span not found in the named file
- **the token really lives at**: `local_runner.py`:60 -> `print(f"\n[Error] Failed to connect to Ollama server: {e}")`

## Case 3 - RIGHT FILE, BAD CITATION  <-- caught only by the span check

- **question** (g0_01, strict contract, `hit` arm): Which file contains a line reading `* ____ the logs for error messages or unexpected results.` , where ____ is a single identifier?
- **evidence token**: `Investigate`
- **file shown to the model**: `notes.md`  ·  **home file**: `notes.md`
- **model answered**: `notes.md`  span `**Step 2: Analyze the genomic pipeline logs:
        * Investigate the logs for error messages or unexpected results.
        *  Examine the logs to identify potential bottlenecks, data inconsistencie`
- **what those lines actually say**: `**Step 2: Analyze the genomic pipeline logs:
        * Investigate the logs for error messages or unexpected results.
        *  Examine the logs to identify po`
- **engine check**: FAIL - span not found in the named file
- **the token really lives at**: `notes.md`:55 -> `* Investigate the logs for error messages or unexpected results.`

## Case 4 - RIGHT FILE, BAD CITATION  <-- caught only by the span check

- **question** (g0_03, strict contract, `hit` arm): Which file contains a line reading `* **Modularity:** The script analysis and execution should be ____ to prevent unintended or unantici` , where ____ is a single identifier?
- **evidence token**: `isolated`
- **file shown to the model**: `notes.md`  ·  **home file**: `notes.md`
- **model answered**: `notes.md`  span `    * **Modularity:** The script analysis and execution should be isolated to prevent unintended or unanticipted modifications.`
- **what those lines actually say**: `    * **Modularity:** The script analysis and execution should be isolated to prevent unintended or unanticipted modifications.`
- **engine check**: FAIL - span not found in the named file
- **the token really lives at**: `notes.md`:70 -> `* **Modularity:** The script analysis and execution should be isolated`

## Case 5 - SWAP BELIEVED  <-- a false affirmation

- **question** (g0_05, strict contract, `fa` arm): Which file contains a line reading `You must execute and display the following four sequential ____ before providing your final output:` , where ____ is a single identifier?
- **evidence token**: `phases`
- **file shown to the model**: `fit_engine.py`  ·  **home file**: `local_runner.py`
- **model answered**: `fit_engine.py`  span `Stage 1: Preattentive Phase (Recursive Workspace Crawl).
 Independently scans state, error ledgers, heuristics, and recursively crawls 
 the entire workspace directory while pruning system noise and e`
- **what those lines actually say**: `Stage 1: Preattentive Phase (Recursive Workspace Crawl).
 Independently scans state, error ledgers, heuristics, and recursively crawls 
 the entire workspace di`
- **engine check**: PASS - span verified
- **the token really lives at**: `local_runner.py`:28 -> `You must execute and display the following four sequential phases befo`

## Case 6 - SWAP BELIEVED  <-- a false affirmation

- **question** (g0_07, strict contract, `fa` arm): Which file contains a line reading `print(f"[*] Polling interval: {poll_interval}s (____ excluded)")` , where ____ is a single identifier?
- **evidence token**: `Staging`
- **file shown to the model**: `.error_ledger.json`  ·  **home file**: `subsystem_daemon.py`
- **model answered**: `.error_ledger.json`  span `behavioral_adjustment": "Enforce mandatory verification of staging outputs before sync", "target_file": ".ai_heuristics.md`
- **what those lines actually say**: `behavioral_adjustment": "Enforce mandatory verification of staging outputs before sync", "target_file": ".ai_heuristics.md`
- **engine check**: PASS - span verified
- **the token really lives at**: `subsystem_daemon.py`:67 -> `print(f"[*] Polling interval: {poll_interval}s (Staging excluded)")`

## Case 7 - SWAP BELIEVED  <-- a false affirmation

- **question** (g0_09, strict contract, `fa` arm): Which file contains a line reading `"http://localhost:11434/api/____",` , where ____ is a single identifier?
- **evidence token**: `generate`
- **file shown to the model**: `fit_engine.py`  ·  **home file**: `local_runner.py`
- **model answered**: `fit_engine.py`  span `self.core_dump_path = os.path.join(self.root, ".core_dump.json")`
- **what those lines actually say**: `self.core_dump_path = os.path.join(self.root, ".core_dump.json")`
- **engine check**: PASS - span verified
- **the token really lives at**: `local_runner.py`:46 -> `"http://localhost:11434/api/generate",`

## Case 8 - SWAP BELIEVED  <-- a false affirmation

- **question** (g0_10, strict contract, `fa` arm): Which file contains a line reading `print(f"[*] [Daemon ____] Updated payload -> {PAYLOAD_PATH}")` , where ____ is a single identifier?
- **evidence token**: `Synchronized`
- **file shown to the model**: `fit_engine.py.old.txt`  ·  **home file**: `subsystem_daemon.py`
- **model answered**: `fit_engine.py.old.txt`  span `self.injection_path = os.path.join(self.root, "staging", "memory_inject.md")`
- **what those lines actually say**: `self.injection_path = os.path.join(self.root, "staging", "memory_inject.md")`
- **engine check**: PASS - span verified
- **the token really lives at**: `subsystem_daemon.py`:62 -> `print(f"[*] [Daemon Synchronized] Updated payload -> {PAYLOAD_PATH}")`

## Case 9 - SWAP CAUGHT

- **question** (g0_00, lines contract, `fa` arm): Which file contains a line reading `print(f"\n[Error] ____ to connect to Ollama server: {e}")` , where ____ is a single identifier?
- **evidence token**: `Failed`
- **file shown to the model**: `fit_engine.py.old.txt`  ·  **home file**: `local_runner.py`
- **model answered**: `fit_engine.py.old.txt`  span `10-27`
- **what those lines actually say**: `self.injection_path = os.path.join(self.root, "staging", "memory_inject.md") /  / def preattentive_extraction(self):`
- **engine check**: FAIL - cited lines do not contain the evidence
- **the token really lives at**: `local_runner.py`:60 -> `print(f"\n[Error] Failed to connect to Ollama server: {e}")`

## Case 10 - SWAP CAUGHT

- **question** (g0_01, lines contract, `fa` arm): Which file contains a line reading `* ____ the logs for error messages or unexpected results.` , where ____ is a single identifier?
- **evidence token**: `Investigate`
- **file shown to the model**: `fit_engine.py.old.txt`  ·  **home file**: `notes.md`
- **model answered**: `fit_engine.py.old.txt`  span `8-9`
- **what those lines actually say**: `...................... . ....................... ..................... / self.heuristics_path = os.path.join(self.root, ".ai_heuristics.md")`
- **engine check**: FAIL - cited lines do not contain the evidence
- **the token really lives at**: `notes.md`:55 -> `* Investigate the logs for error messages or unexpected results.`

## Case 11 - SWAP CAUGHT

- **question** (g0_02, lines contract, `fa` arm): Which file contains a line reading `* **Unintended Interactions:**  Interactions ____ different modules must be carefully reviewed to avo` , where ____ is a single identifier?
- **evidence token**: `between`
- **file shown to the model**: `.error_ledger.json`  ·  **home file**: `notes.md`
- **model answered**: `.error_ledger.json`  span `6-7`
- **what those lines actually say**: `................ ........ .... ... ............ / "post_mortem": {`
- **engine check**: FAIL - cited lines do not contain the evidence
- **the token really lives at**: `notes.md`:75 -> `* **Unintended Interactions:**  Interactions between different modules`

## Case 12 - SWAP CAUGHT

- **question** (g0_03, lines contract, `fa` arm): Which file contains a line reading `* **Modularity:** The script analysis and execution should be ____ to prevent unintended or unantici` , where ____ is a single identifier?
- **evidence token**: `isolated`
- **file shown to the model**: `fit_engine.py`  ·  **home file**: `notes.md`
- **model answered**: `fit_engine.py`  span `9-9`
- **what those lines actually say**: `self.heuristics_path = os.path.join(self.root, ".ai_heuristics.md")`
- **engine check**: FAIL - cited lines do not contain the evidence
- **the token really lives at**: `notes.md`:70 -> `* **Modularity:** The script analysis and execution should be isolated`

## Case 13 - REFUSAL

- **question** (g0_08, strict contract, `fa` arm): Which file contains a line reading `print("[!] Ensure the Ollama ____ service is running.")` , where ____ is a single identifier?
- **evidence token**: `background`
- **file shown to the model**: `.core_dump.json`  ·  **home file**: `local_runner.py`
- **model answered**: `NONE`  span ``
- **engine check**: PASS - refusal
- **the token really lives at**: `local_runner.py`:61 -> `print("[!] Ensure the Ollama background service is running.")`

## Case 14 - REFUSAL

- **question** (g0_15, strict contract, `fa` arm): Which file contains a line reading `"snippet": item["content"][:800].replace('\n', ' ')  # Expanded snippet ____ for deep inspection` , where ____ is a single identifier?
- **evidence token**: `window`
- **file shown to the model**: `local_runner.py`  ·  **home file**: `fit_engine.py`
- **model answered**: `NONE`  span ``
- **engine check**: PASS - refusal
- **the token really lives at**: `fit_engine.py`:55 -> `"snippet": item["content"][:800].replace('\n', ' ')  # Expanded snippe`

## Case 15 - CORRECT, citation verified

- **question** (g0_00, lines contract, `hit` arm): Which file contains a line reading `print(f"\n[Error] ____ to connect to Ollama server: {e}")` , where ____ is a single identifier?
- **evidence token**: `Failed`
- **file shown to the model**: `local_runner.py`  ·  **home file**: `local_runner.py`
- **model answered**: `local_runner.py`  span `58-60`
- **what those lines actually say**: `............. / except Exception as e: / print(f"\n[Error] Failed to connect to Ollama server: {e}")`
- **engine check**: PASS - lines 58-60 verified
- **the token really lives at**: `local_runner.py`:60 -> `print(f"\n[Error] Failed to connect to Ollama server: {e}")`

## Case 16 - CORRECT, citation verified

- **question** (g0_01, lines contract, `hit` arm): Which file contains a line reading `* ____ the logs for error messages or unexpected results.` , where ____ is a single identifier?
- **evidence token**: `Investigate`
- **file shown to the model**: `notes.md`  ·  **home file**: `notes.md`
- **model answered**: `notes.md`  span `50-56`
- **what those lines actually say**: `.. .......... / . ...... .. ........ ... ....... ...... .. ... ..... .......... ......... / .  ...... ... .......... ........ .... ... ........ .......`
- **engine check**: PASS - lines 50-56 verified
- **the token really lives at**: `notes.md`:55 -> `* Investigate the logs for error messages or unexpected results.`

## Case 17 - CORRECT, citation verified

- **question** (g0_02, lines contract, `hit` arm): Which file contains a line reading `* **Unintended Interactions:**  Interactions ____ different modules must be carefully reviewed to avo` , where ____ is a single identifier?
- **evidence token**: `between`
- **file shown to the model**: `notes.md`  ·  **home file**: `notes.md`
- **model answered**: `notes.md`  span `70-76`
- **what those lines actually say**: `* **Modularity:** The script analysis and execution should be isolated to prevent unintended or unantici / ..... .............. / `
- **engine check**: PASS - lines 70-76 verified
- **the token really lives at**: `notes.md`:75 -> `* **Unintended Interactions:**  Interactions between different modules`

## Case 18 - CORRECT, citation verified

- **question** (g0_03, lines contract, `hit` arm): Which file contains a line reading `* **Modularity:** The script analysis and execution should be ____ to prevent unintended or unantici` , where ____ is a single identifier?
- **evidence token**: `isolated`
- **file shown to the model**: `notes.md`  ·  **home file**: `notes.md`
- **model answered**: `notes.md`  span `70-70`
- **what those lines actually say**: `* **Modularity:** The script analysis and execution should be isolated to prevent unintended or unantici`
- **engine check**: PASS - lines 70-70 verified
- **the token really lives at**: `notes.md`:70 -> `* **Modularity:** The script analysis and execution should be isolated`
