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

## F2 re-run (wave-fix proof) — 2026-09-18 ~12:00
- Reran F2 mission after label-strip fix. Result: 2/2 TODOs, 2/2 wave, MISSION SCORE 100/100 (was 60/100).
- Fix proven end-to-end on live free models. No tree change (verification only).
- No stray procs (pgrep self-match false positive, confirmed via ps).
## P5a plan (appended) — parallel explorers + --max-verify
Tier: HEAVY (new concurrency in execution loop). No plan file -> self-review + FRIDAY review paste-block at end (reviewer loop, P3 precedent).
Goal: architect tags TODOs [role:X] (Ch.4: architect tags each TODO — missing until now); run_loop(parallel=) runs explorer-role TODOs concurrently via ThreadPoolExecutor (stdlib); wave retry loop extracted to engine.verify_wave(b, max_verify); CLI --parallel + --max-verify N (default 3).
Criteria:
- C1: role tag parsed ("[role:explorer] recon" -> explorer, untagged -> builder) — test seam
- C2: parallel overlap proven at seam (2 explorers x 0.5s sleep complete <0.9s wall, both flipped, runs.log 2 rows) — fake runner, no live burn
- C3: sequential default unchanged (existing 14 tests pass unmodified)
- C4: max_verify controls fix retries (always-fail wave + max_verify=2 -> fix called 2x)
- C5: suite all green + keyless grep clean + --help shows flags
SURFACE: tony --help + --models live. No live model burn (threading proven at seam; live burn unjustified for this slice).
Teardown: tests use fake runners + echo/false only; per-test tmpdirs removed.
## 12:4x — P5a GREEN, COMMITTED c4928b2 (+873ce1f hygiene)
- RED captured: AttributeError todo_role + LSP no-param/no-attr (6 diagnostics) + runtime AttributeError
- GREEN: 18/18 (14 prior unmodified + 4 new). C1 tag parse; C2 overlap (2x0.5s explorers <0.9s wall, 2 runs.log rows); C3 builders sequential (>=0.9s wall under parallel=True); C4 max_verify=2 -> fix 2x
- C5: --help shows both flags; keyless grep clean; zero hardcoded ids; live --models 7 models through new code path
- SURFACE: --help + --models live. No live model burn (threading proven at seam).
- BONUS FIND (mine): lib/report.py never committed in P4 (tracked-files audit) — fresh clone would crash cmd_mission. Committed 873ce1f + .omo/ gitignored (2 harness strays already in history, left alone — no rewrite).
- No stray procs (all tests use fake runners + echo/false; tmpdirs removed per-test).

## P5a review disposition (2026-09-18, FRIDAY read-only -> VISION verify)
- Verdict: PASS unconditional, 0 ISSUES, 8 notes. Report: ~/.fleet/out/tony-p5a-review.md.
- VISION re-verified: suite EXECUTED 18/18 GREEN (closes FRIDAY's read-only gap); report.py committed-identical (cmp); secrets grep clean (no api_key/Auth/Bearer/raw-HTTP); empty wave -> [] vacuous pass; max_verify=0 runs once (Note, no criterion defines 0-semantics).
- _exec_one demote branches match old inline loop; tag-dispatch delta intended. Notes 1-8 accepted as P5b+ backlog, none criterion-breaking. No code changed in this step.

## P5b plan (appended) — review-notes hardening, no live burn
Tier: LIGHT (single-file engine slice, all context loaded; no plan file -> self-review).
Goal: close FRIDAY's 8 P5a notes (tony-p5a-review.md): shared resolve_role (n1),
unknown-tag log (n2), verify_wave last-fix gate + 0-semantics + None-log (n3/n4),
parallel abort containment (n5), timing margins (n6), shell=True trust comment (n7),
drop now_stamp (n8). --resume/TUI/watch/plan-gates stay P5c+.
Criteria:
- C1: resolve_role precedence (explicit > tag > builder) + single log line — test
- C2: max_verify=N buys N attempts and N-1 fixes; fix_fn=None honest log — test
- C3: one TODO fs blowup -> [BLOCKED], mission continues — test
- C4: all 18 prior tests pass (2 updated for new semantics/margins) — suite
- C5: keyless grep clean, zero hardcoded ids, live --models 7 models, --help text
SURFACE: --help + --models live. No live model burn (fake runners + echo/false).
## 12:2x — P5b GREEN, 23/23
- RED captured: no resolve_role + silent unknown tag + fix 2x on max_verify=2 + misleading 'feeding fix' with fix_fn=None + dead now_stamp
- GREEN: 23/23 (18 prior: 16 unmodified, test_p5 timing margins 0.5->0.6s/0.9->1.0s + max_verify fix-count 2->1; 5 new in test_p5b.py)
- C5: keyless clean, no hardcoded ids, --help shows new text, live catalog 7 models + role map through new code
- LSP flagged todo_role/resolve_role/parallel/verify_wave as unknown — stale cache, disproven by direct import (all True) + 23/23 execution

## P5c-1 plan (appended) — --resume + --keep-going (mission continuity; replaces Hermes/Cline session resume)
Tier: LIGHT (CLI + 2 engine helpers, all context loaded; no plan file -> self-review).
Goal: tony --resume <slug> loads ~/.tony/boulders/<slug>.md and continues from first unchecked box (no second architect call, no extra model burn on resume path itself); --keep-going controls wave gating on BLOCKED TODOs.
Direction note (user order): tony replaces hermes+cline+opencode+omo (kept, unused). Mapping holds: OMO discipline embedded, opencode CLI only transport, Cline keyless pattern mirrored, Hermes fleet citizenship. No design change.
Criteria:
- C1: resume skips checked boxes, executes only unchecked (fake-runner proof, no live burn)
- C2: BLOCKED gate — has_blocked/should_run_wave: blocked+no-flag -> wave skipped; blocked+--keep-going -> wave runs; clean -> wave runs either way
- C3: save/load round-trip preserves boxes (resume fidelity on disk)
- C4: full suite green + keyless clean + --help shows flags + live --models 7 models
SURFACE: --help + --models live + on-disk boulder round-trip. No live model burn (resume e2e would spend calls; seam proof is the faithful evidence for continuity).
Teardown: fake runners + echo/false only; per-test tmpdirs removed; no procs.

## 12:5x — P5c-1 GREEN, COMMITTED c3abcab
- RED captured: should_run_wave unknown (LSP; old-file LSP noise = stale cache, ignored)
- GREEN: 26/26 (23 prior unmodified + 3 new: resume-skips-done, blocked-gate, save/load round-trip)
- C1 resume skips checked (fake-runner: 1 call for the 1 unchecked TODO only)
- C2 gate: blocked+no-flag -> skip; blocked+keep-going -> run; clean -> run either way
- C3 round-trip boxes survive save/load
- SURFACE LIVE (zero model burn): --resume p5c-resume-proof (1/1 done + echo wave) -> 100/100, no role calls; --help shows --resume/--keep-going; keyless grep clean; --models 7 models live
- Proof residue cleared (boulder+report+workdir); commit c3abcab atomic

## P5c-2 plan (appended) — progress + critic_gate + watch + cmd wiring
Tier: LIGHT (lib/watch.py + engine.critic_gate + boulder.progress + tony --watch wiring; all context loaded; no plan file -> self-review).
Goal: land pure render_snapshot + tail_lines + work_files helpers, critic_gate gate function, boulder.progress semantics, and tony --watch CLI wiring with join-bug fix `_builder_fix([crit...])`.
Criteria:
- C1: watch.render_snapshot produces pane headers (TODOs/wave/runs/roster) + truncates to <=200 chars — test
- C2: watch.tail_lines + work_files helpers — test
- C3: critic_gate("PASS")=="PASS", case-insensitive word-boundary only, None/empty/"BYPASS"/"PASSED" -> "ISSUES" — test
- C4: boulder.progress returns {done,total,waved,wavetotal,score,blocked} — test
- C5: tony --watch <slug> + --once + --interval + --timeout wired and live — verify
- C6: join-bug fix: `_builder_fix([crit["output"]])` moved inside `if gate == "ISSUES"` block (was outside, ran unconditionally) — verify by code review
- C7: suite 42/42 green (26 prior + 16 new), keyless grep clean, zero hardcoded ids, live --help + --models
SURFACE: --help + --models live + --watch once. No live model burn (watch polls local boulder only).
Teardown: fake runners + echo/false only; per-test tmpdirs removed; no procs.
## 12:5x — P5c-2 GREEN, COMMITTED (pending)
- RED captured: progress/critic_gate/watch symbols absent (test_p5c2.py 16 tests)
- GREEN: 42/42 (26 prior unmodified + 16 new). C1 render_snapshot panes + truncation; C2 tail_lines/work_files; C3 critic_gate word-boundary; C4 progress dict shape; C5 --watch once live; C6 join-bug fix _builder_fix inside ISSUES block; C7 suite 42/42, keyless clean, --help + --models live
- SURFACE: --help + --models + --watch once live. No live model burn (watch polls local boulder only).
- Join-bug fix: `_builder_fix([crit["output"]])` was outside `if gate == "ISSUES"` in cmd_mission, running unconditionally on every mission with >=3 TODOs. Moved inside the block. Verified by code review + test_p5c2.py.
- Exit proofs: 2 missing / 0 done-once / 1 open-once (watch --once exits 1 when boulder incomplete, 0 when done; --watch poll exits 0 on completion).
- Suite 42/42 green. No live model burn.
## Now
P5c-2 done. Awaiting user: P5d (config system) or stop.

## P5d — per-role model config + auto-setter (2026-09-18)
- RED: tests/test_p5d_config.py, 8 tests (5 ImportError lib.config + 3 AttributeError assign_roles_with_sources). Fixed shared-tmpdir flake (stale /tmp/tony-test-p5d-home corrupt json) — hermeticity note for future tests.
- GREEN: lib/config.py (load/save/get_roles/set_role/clear_role/clear_roles/validate, $HOME at call time, KeyError/re.error fail-fast, corrupt→stderr+defaults).
- Tiers: resolve_override + assign_roles_with_sources (None→legacy-identical, dict→enriched {model,source}); enriched path skips (not raises) on empty-tier+empty-spare; legacy path keeps RuntimeError. --models map byte-identical with no config.
- CLI: --set-role/--clear-role/--show-config/--auto-config + [override] marks; malformed→exit 2 pre-write; no-match→stderr fallback; corrupt config→warn+defaults exit 0.
- Contract live: H1 set+show (override) / H2 --models mark / H3 auto-config preserves opencode_bin; E1 no-match fallback / E2 bad regex exit 2 / E3 unknown role exit 2 / E4 corrupt warn+proceed; R1 legacy identity / R2 50/50 green / R3 keyless + patterns-only greps clean.
- Suite 50/50 green. No live model burn (cached `opencode models` reads only). ~/.tony/config.json removed after verification.
## Now
P5d done. Tree at P5d landing commit.

## Hotfix — _builder_fix UnboundLocalError in cmd_mission (live F2 found, 2026-09-18)
- RED (live): F2 re-proof crashed after builder TODOs with UnboundLocalError — gate block called _builder_fix before its def (missions with >=3 TODOs + critic ISSUES). cmd_resume order was already correct.
- GREEN: moved def above gate block (mirrors resume); AST order-check both functions OK; suite 50/50; F2 re-run 2/2 TODOs + 2/2 wave (cat + test -f) 100/100, file HELLO FROM TONY exact.
- Honest gap: re-run had 2 TODOs (critic skipped), so the ISSUES+fix call path itself was proven by AST-order + suite, not re-triggered live.
- Residue cleared (~/tony-e2e, boulders, workdirs, fleet reports); runs.log kept as ledger.

## Gate-path regression pin (2026-09-18, closes F2 honest gap)
- Extracted apply_critic_gate(b, gate, keep_going, fix_fn, critic_output) into engine.py; cmd_mission calls it with fix_fn as parameter — call-before-def crash structurally impossible.
- tests/test_gate.py: 4 pins (PASS clean / ISSUES fix-once+hold / keep-going override / None-fix honest hold). Suite 54/54.
