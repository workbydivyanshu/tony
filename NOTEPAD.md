# Ultrawork Notepad — Tony P1 (catalog + tiers + --models/--status)
Started: 2026-09-18T03:3x+05:30

## Plan (exhaustively detailed)
1. Scaffold ~/tony/ (tony CLI stub, lib/, tests/) + NOTEPAD — verify by ls
2. tests/test_p1.py: fixture catalog parse + tier assignment — verify RED (ModuleNotFoundError) captured below
3. lib/catalog.py: opencode models reader, 60s TTL cache in ~/.tony/ — verify GREEN
4. lib/tiers.py: tier patterns (ported from fleet-models-sync) + roles map — verify GREEN
5. tony CLI: --models, --status wired — verify live output
6. Commit P1 atomic (aubade-style authorship) + update boulder tony-v01.md

## Success criteria + QA scenarios
- C1: `tony --models` prints live opencode/* models + tier map — verify by stdout, ≥7 models
- C2: `tony --status` shows catalog + assignments + boulders — verify by stdout
- C3: no hardcoded model ids (delete union-alpha from disk? no — verify grep shows patterns only)

## Now
Step 1: scaffold

## Todo
- scaffold ~/tony + NOTEPAD
- test_p1.py RED capture
- catalog.py GREEN
- tiers.py GREEN
- CLI live verify C1/C2/C3
- commit + boulder update
- teardown: no stray procs (none spawned)

## Findings
- Live catalog = 7 models (union-alpha absent tonight — patterns self-heal, never hardcode)
- fleet-models-sync TIERS ported verbatim; roles table from scripture Ch.3

## 03:5x — P1 GREEN, COMMITTED 7b1a72d
- RED captured: ImportError catalog (no lib yet) + pluggy missing (no pytest in env — plain-assert runner instead)
- GREEN: 3/3 tests pass; C1 7 models + 6 role assignments live; C2 --status JSON good; C3 zero ids/keys (grep clean)
- P1 per Ch.6 verify: expected 8 models, got 7 (union-alpha absent live; patterns self-heal, noted)
## Now
P1 done. Awaiting user: P2 (boulder.py + architect + --dry-run) or stop.
## P2 plan (appended 03:5x)
Goal: lib/boulder.py (fleet-format read/write) + architect prompt + tony --dry-run "mission" -> sane boulder file.
Criteria:
- C1: boulder round-trip: write sample TODOs+wave, re-read, boxes flip — verify by test
- C2: --dry-run produces ~/.tony/boulders/<slug>.md with 3-7 TODOs + 2-4 wave cmds — verify by file content
- C3: no execution in dry-run (zero opencode calls) — verify by runs.log absent/empty
Steps: test_boulder.py RED -> boulder.py GREEN -> roles.py architect template -> CLI --dry-run GREEN -> commit.
## Now
test_boulder.py RED capture
## 03:5x — P2 GREEN, COMMITTED 71e91c8
- RED: ImportError boulder (pre-lib) captured
- GREEN: 5/5 (3 P1 + 2 boulder round-trip/new-log)
- C1 boulder round-trip incl. box-flip + re-parse: PASS
- C2 --dry-run fizzbuzz -> ~/.tony/boulders/fizzbuzz.md (title+TODO+wave+log): PASS
- C3 zero execution (no runs.log): PASS
## Now
P2 done. Awaiting user: P3 (engine + role calls) or stop.
## P3 plan (appended)
Tier: HEAVY (new external integration: subprocess opencode; per directive). No plan file -> self-review, no reviewer loop.
Goal: lib/engine.py (role_call via `opencode run`, demote+retry, boulder flip/log, runs.log) + tony "MISSION" one-shot (architect plan -> execute -> wave basic).
Criteria:
- C1: role_call runs subprocess, captures output+duration, writes delegate file — verify by test w/ fake runner
- C2: engine loop flips boxes + logs + demotes once on failure then BLOCKED — verify by test
- C3: runs.log row per call (ts, role, model, status, duration) — verify by test
- C4 E2E: tony "reply with TONY ONLINE" works, free model only — verify live (scripture F1)
Steps: test_engine.py RED -> engine.py GREEN -> CLI mission wired -> live C4 -> commit.
## Now
test_engine.py RED capture
## 03:5x — P3 GREEN, COMMITTED d1548cc
- RED: ImportError engine (pre-lib) captured
- GREEN: 7/7 (5 prior + role_call + demote-retry-then-ok with 2-line runs.log proof)
- C4/F1 LIVE: tony 'reply with TONY ONLINE' — architect (nemotron-3-ultra, 56s) planned 1 TODO + F1 wave; builder (84s) wrote response.txt='TONY ONLINE'; boulder 1/1 done; runs.log row captured. Cleanup: response.txt removed, .gitignore added, no fleet leak (~/.fleet/boulder/tony-online.md NOT created — opencode wrote to its own cwd only... verified absent)
## Reviewer verdict (FRIDAY, tony-p3-review.md): ISSUES — all verified, dispositions below
- ISSUE-1 (BLOCKED branches untested): FIXED — added test_loop_double_fail_blocked + test_loop_no_fallback_blocked; 9/9 green. Also found + fixed: tests were non-hermetic (fixed /tmp dirs accumulated rows across runs and failed my own re-run — now shutil.rmtree per test).
- ISSUE-2 (exit-code-only done-ness, wave never executed): CONFIRMED REAL, deferred to P4 by design (critic + verification wave is P4's entire job per scripture Ch.6). F1's response.txt evidence was captured live (I read the file before cleanup), but the engine cannot prove artifacts — P4 fixes the loop, not the claim.
- ISSUE-3 (architect call bypasses runs.log): FIXED — logging moved INTO role_call (single choke point); run_loop passes runslog through; demote path no longer double-appends.
- ISSUE-4 (ANSI noise in saved boulder): CONFIRMED, deferred to P4 (sanitize architect output at parse boundary when the engine owns the wave).
- BONUS FIND (mine, during verification): opencode's builder wrote .fleet/boulder/tony-online.md relative to ITS cwd — a real fleet leak I had claimed absent. Found via repo-wide glob, removed (git rm), verified. My P3 self-review claim was wrong; FRIDAY's suspicion was right.
- Committed 123fd1f. NOTEPAD current.
## Now
Reviewer loop closed. Awaiting user: P4 or stop.
## P4 plan (appended)
Tier: HEAVY (closes ISSUE-2/4 by changing the execution loop). No plan file -> self-review.
Goal: critic role + verification-wave execution + sanitize boundary + report.py (scribe + MISSION SCORE) + tony --resume/--status already there.
Criteria:
- C1: wave items execute as shell commands; pass/fail flips boxes; failure feeds builder once then re-runs — verify by test w/ fake runner + real echo/false cmds
- C2: architect output sanitized at parse boundary (ANSI stripped, transcript chrome dropped) — verify by test
- C3: report writes ~/.fleet/out/tony-<slug>.md with mission/models/TODOs/wave + MISSION SCORE — verify by test
- C4 E2E (scripture F2): tony mission creates+verifies file — verify live
Steps: test_p4 RED -> engine wave + sanitize + report.py GREEN -> CLI wired -> live C4 -> commit.
## Now
test_p4 RED capture
## Todo
- test_p4 RED
- wave execution + sanitize + report GREEN
- CLI wired + live C4
- commit + notepad
## F2 e2e exposed real P4 bug (wave F-labels) + opencode-bin hardening
- F2 run: 3/3 TODOs but 0/2 wave, auto-score 60/100. Root cause: run_wave passed "F1. <cmd>" incl. label to shell -> "F1.: command not found" x3 attempts. Work was never broken (critic independently re-ran: EXISTS + CONTENT_MATCH, 15 bytes exact). Critic also correctly flagged TODO 3 done on exit-code with garbage evidence (ISSUE-2 honesty gap, still known limitation; wave is the gate).
- RED: F1-prefixed wave item -> [False] reproduced live. GREEN: F_LABEL strip at execution boundary (labels kept in file for readability) + test_wave_strips_f_labels. Suite 13/13, then 14/14 after resolve_bin.
- Opencode-CLI lane (user: "cline does it, tested"): tony already rides `opencode run` only (no raw HTTP, architectural law). Hardened: catalog.resolve_bin() = explicit > $OPENCODE_BIN > ~/.tony/config.json > shutil.which > "opencode"; role_call + live_catalog both resolve through it. New test_resolve_bin. Live --models re-verified through new path (7 models).
- Note on test comment (hook): the F-label test carries a one-line provenance comment naming the e2e bug it pins. Kept deliberately: regression-pin comments that name the failure they guard are necessary documentation, not noise.
