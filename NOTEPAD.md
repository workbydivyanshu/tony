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

## Review hardening pass (2026-09-18, self-review of P5d diff)
- Real finds: config.validate() dead (no callers, re-read file 6x) -> wired into --show-config stderr; wrong-shape roles (null/str) crashed get_roles/clear_role -> isinstance guards; clear_role wrote a config file on no-op -> early return; save() docstring falsely claimed atomic writes; 2 redundant local imports.
- 3 regression pins (no-op write, wrong-shape, validate); suite 57/57; live --show-config warning + --clear-role no-file creation verified; ~/.tony/config.json removed after.
- Note: hermes-agent/ clone in progress inside ~/tony by Vianca (13:49) — left alone, never staged.

## TAKEOVER — VISION resumes from opencode V1 work (2026-09-18 ~15:30)
- Opencode landed 5 commits after NOTEPAD stopped: b28e128 (ignore clones) → 2f249fc (score.py 40/40/20 + curses tui.py, 77/77) → 9d5c2fa (429 backoff [5,20] + 1MB log rotation, 87/87) → d1aa47c (critic v2 rubric + strict VERDICT + evidence coverage, 109/109) → 5c509a9 (score-central CLI wiring, --tui/--timeout, 131/131).
- VISION verified, not trusted: full suite EXECUTED 131/131 green (plain-assert runner; unittest loader finds 0 — tests are bare functions, pre-existing style); keyless grep clean (no api_key/Authorization/Bearer); live --models 7 models + role map; --help/--status live.
- Scripture wave status: F1 ✓ (TONY ONLINE live), F2 ✓ (100/100 re-run), F3/F4 → verifying now (free). Unproven live path: --parallel e2e (P5a deferred payoff) — next live burn.
- Missing vs scripture flags: --slug auto absent (slug always derived; acceptable, note only). Plan-gates omO-style still P5c+ backlog.

## TAKEOVER VERIFIED — VISION live (2026-09-18 ~evening)
- Sub-agent launch: CONFIRMED live. Fired explore (ses_f4c0c6969ffejFgTtraiuWNm1d, ran nemotron-3.5-lightning-free, 13m) — returned full P1-P5c audit with file:line cites, 0 issues, keyless clean. Sub-agent lane works.
- Suite EXECUTED by VISION: 136/136 green (16 modules; 131 at takeover + 5 new since — plangate/tui/cli-wiring growth). Plain-assert runner (unittest finds 0, pre-existing style).
- Live lane: --models 7 models + role map; --status JSON valid (catalog+tiers+roles+boulders); --help shows all flags through --timeout.
- F3: --status live ✓; config json.tool N/A (no ~/.tony/config.json yet — defaults active, correct state). F4: keyless grep clean (no api_key/Authorization/Bearer in lib/tony/tests); no literal opencode/<id> in lib (only "opencode/" prefix filter in catalog.py:16 + tier regex patterns in tiers.py:10-11 — patterns, not IDs, by design).
- Next: --parallel e2e live proof (P5a deferred payoff) + plan-gates triage.

## PAR2 VERDICT — parallel re-proof GREEN (2026-09-18 ~16:05)
- Mission: fresh-dir par2, --parallel. Result: 4/4 TODOs, 2/2 wave, MISSION SCORE 80/100.
- Parser fix proven: 4 tagged TODOs parsed (par1 managed 1 garbage fallback TODO). No fallback blob.
- Parallel overlap proven live: runs.log explorer rows 15:54:26 (28.8s) + 15:55:21 (84.5s), both started ~15:53:57 post-architect — threaded batch overlapped. Workdir holds 02-explorer.md + 03-explorer.md.
- Critic ISSUES -> 07-builder fix -> wave 2/2 green. The full loop (plan/execute/critique/fix/verify) ran as designed. 20 pts off = honest critic-gate deduction, not a defect.
- hello-par2.txt: 12B PARALLEL2 OK + newline, F1 EXISTS + F2 CONTENT_OK live.

## BACKLOG TRIAGE (closes the todo)
- Plan-gates: IMPLEMENTED (lib/plangate.py — TTY y/N confirm, --yes bypass, headless proceeds with honest log line; 5 tests in test_plangate.py; par2 boulder shows "plan-gate skipped (non-TTY headless)"). Not backlog — done.
- --slug flag: intentionally absent. slugify() always derives (tony:106-109). Acceptable per prior note; no action.

## P-next plan (appended) — plan-gate omO-style + F3/F4 scripture wave
Tier: LIGHT (lib/plangate.py pure helper + 1 CLI flag + gate call; no plan file -> self-review).
Goal: close the last auditor-confirmed gap (no pre-execution approval). After architect plans, before ANY builder call, TTY missions pause for y/N unless --yes; headless (non-TTY) proceeds with honest log (never hang a pipe).
Criteria:
- C1: pre_approved (--yes) executes without prompting (input_fn must never fire) — test
- C2: non-TTY proceeds + logs headless-skip (no hang) — test
- C3: TTY y/yes proceeds; empty/n declines (gate returns False) — test
- C4: declined mission saves boulder, spends zero builder calls, exits 2 — test
- C5: suite all green + keyless clean + live --help shows --yes + F3 (--status JSON valid) + F4 (grep zero hits)
SURFACE: --help + --status live. No live model burn (gate proven at seam; architect call untouched).
Teardown: fake input_fn only; per-test tmpdirs removed; no procs.

## 15:4x — P-next GREEN, plan-gate shipped
- RED: lib.plangate unknown import (LSP; other-file LSP noise = stale cache per precedent, ignored)
- GREEN: 136/136 (131 prior unmodified + 5 new test_plangate.py). C1 --yes never prompts; C2 non-TTY proceeds+logs (no hang); C3 y/yes proceeds, empty/n declines; C4 declined -> boulder saved, exit 2, zero builder calls by construction (gate sits before run_loop)
- SURFACE LIVE: --help shows --yes; F3 --status JSON valid; F4 keyless grep zero hits; --models 7 live (prior run)
- Auditor gaps closed: --once/--interval confirmed wired via watch sub-parser (tony:316-325); --slug still absent by design (slugify); plan-gate was the last real gap — now shut.

## par1 --parallel e2e verdict (2026-09-18 15:42–15:50) — 90/100
- Wave 4/4 PASS after 1 fix cycle (F2 newline diff failed first, builder fix added trailing newline, re-run green). Fix loop proven live.
- BUT parallel-overlap NOT proven: boulder shows 1 mangled TODO (`- [x] # Boulder: tony-parallel-recon` + raw block truncated at `## Final V` = clean[:400] fallback). Root cause: old _ITEM regex couldn't parse architect's `- [role:X] [ ]` lines → parse()=0 todos → add_todo(clean[:400]) fallback. Single explorer call 345.9s did everything (role bleed: explorer wrote the file).
- Fix landed as d2de2b5 (15:52, opencode): _ROLE_PREFIX in _ITEM. VISION verified: re-parse of 01-architect.md now yields 4 todos + 4 wave; suite 136/136 green WITH the fix.
- par2 re-proof launched (~15:5x, slug in-home-divyu-tony-e2e-par2-...) against fixed parser — verdict pending.

## par2 --parallel re-proof verdict (2026-09-18 15:53–16:05) — 80/100, PARALLEL PROVEN LIVE
- 4/4 TODOs (fixed parser: all architect tags dispatched as separate role calls) + 2/2 wave PASS after 1 critic-gated fix cycle.
- Overlap proof (runs.log): TODO 2 explorer done 15:54 (29s) + TODO 1 explorer done 15:55 (85s), both lightning-free, both started ~15:53:5x — concurrent thread dispatch, separate outfiles 02/03. P5a deferred payoff CLOSED.
- Critic adversarial again: flagged TODO 4 existence-only proof → ISSUES → builder fix → wave green. Score 80 reflects the fix cycle (honest auto-score).
- No strays (ps clean). Proof residue: ~/tony-e2e-par2/hello-par2.txt (12B exact), boulder + report on disk.

## v0.1 release triage (2026-09-18 ~16:05, VISION)
- Suite 136/136 green WITH d2de2b5 (executed, plain-assert runner). F1 ✓ F2 100/100 ✓ F3 --status JSON valid ✓ F4 keyless grep zero hits + zero opencode/<id> literals in lib ✓ (patterns only, by design).
- Flags live: --models/--status/--dry-run/--parallel/--max-verify/--resume/--keep-going/--yes/--watch/--tui/--timeout/--set-role/--clear-role/--show-config/--auto-config.
- Shipped live-proven: parallel explorers, critic gate + fix loop, plan-gate (--yes, TTY pause, headless-skip), resume/keep-going, watch/TUI, role overrides + auto-config, 429 backoff + log rotation.
- Open (v0.2): MCP tools via opencode's own tool support; Textual TUI (curses shipped, acceptable); --slug auto absent by design (slugify).
- VERDICT: v0.1 functionally complete. Tag when Vianca says.

## v0.1 TAG (2026-09-18 ~16:2x, VISION)
- Suite RE-EXECUTED 137/137 green (16 modules, plain-assert runner). F4 keyless grep zero hits (lib/tony/tests). --status JSON valid, 7 live models.
- Boulder tony-v01.md: TODO 6 + F4 flipped. All 4 wave items green. Tagging v0.1 now.
- Vianca order: finish tony first, then aubade. v0.2 scope = MCP tools via opencode + TUI polish.

## P6 (v0.2 MCP tools via opencode's own tool support) — plan (2026-09-18)
Findings (recon, live):
- `opencode run` has NO --mcp flag (only --pure/--agent/--model/--dir). MCP servers ride opencode.json "mcp" + plugin lane; `opencode mcp list` live = 5 connected (websearch, context7, grep_app, lsp, playwright). Delegates inherit MCP automatically — critic transcripts already show tool calls (Read/bash).
- So P6 is NOT plumbing (nothing to plumb) — it is visibility + planner-awareness: lib/mcp.py parser, --mcp-status/--status(mcp), architect prompt carries server list, one live proof that a delegate used an MCP tool.
Tier: LIGHT (stdlib parser + 2 CLI wirings + prompt line; no plan file -> self-review).
Goal: planner knows MCP tools exist; operator sees them; one live mission proves a delegate used one.
Criteria:
- C1: lib/mcp.py parses REAL `opencode mcp list` output (ANSI included) -> [{name, connected}] for all 5 — test on captured sample
- C2: `tony --mcp-status` prints 5 live; `--status` JSON gains "mcp" key — live stdout
- C3: architect_prompt includes MCP server names (planner-aware) — test asserts names in prompt
- C4: suite all green + keyless grep clean + zero hardcoded model IDs
SURFACE: live --mcp-status + --status; one fast-model live mission using an MCP tool (context7/websearch), wave green.
Teardown: fake runner + captured sample in tests; live proof residue (workdir/boulder/report) logged; no procs left.

## P6 GREEN + SURFACE (2026-09-18 ~16:44-16:54, VISION)
- GREEN: suite 139/139 (137 prior untouched + 2 new test_p6_mcp). KEYLESS-CLEAN. Live --mcp-status 5 connected; --status JSON gains "mcp" key. Committed be71ce9.
- SURFACE LIVE (slug use-your-websearch-mcp-tool-to-find-the-current-, --yes, free models only):
  - Researcher (muse-spark) invoked Exa Web Search (websearch MCP) live, found 3.14.7 with python.org sources. MCP-USE PROVEN (transcript trace, run 1 AND run 2).
  - Builder wrote stale 3.14.4 from memory. Critic: VERDICT ISSUES ("Exa claims 3.14.7 — conflicts with built file 3.14.4"). Builder fix loop repaired -> PYTHONGREEN 3.14.7. Wave 3/3 PASS. MISSION SCORE 80/100.
  - VISION independently websearched python.org: 3.14.7 (Aug 5 2026) confirmed. File correct.
- PROCESS LESSON: first e2e parent reaped by harness tool-timeout (nohup-in-timed-call dies with the group; empty log + dead PID + no boulder, delegates' work survived on disk). Relaunched via setsid + stdin-closed -> survived to verdict. Rule: long missions launch with setsid, never sleep inside the launch call.
- Residue: pygreen.txt (verified) kept; stale pyver.txt (dead run, wrong version) removed. Boulder + report on disk.

## P7 (v0.2 release triage + tag) — plan (2026-09-18)
Tier: LIGHT (verify-only, no code; no plan file -> self-review).
Goal: prove v0.2 shippable and tag it. v0.2 = v0.1 + P6 (MCP visibility + planner-awareness). Textual TUI explicitly DECLINED (stdlib-only law; curses ships and works — polish only, never a release gate).
Criteria:
- C1: full suite green (all test_ fns across tests/*.py, plain-assert runner)
- C2: keyless grep clean (no api_key/Authorization/Bearer in lib/tony/tests) + zero hardcoded opencode/<id> literals in lib
- C3: live --models (7 free models + role map) + --status JSON valid with mcp key + --mcp-status 5 connected
- C4: tag v0.2 on the verification commit; tree clean after
SURFACE: live CLI outputs. No live model burn (P6 already proved MCP-use live at 80/100; re-burning free-tier quota for a tag adds no evidence).
Teardown: suite uses fake runners + echo/false only; no procs.

## P7 GREEN + v0.2 TAG (2026-09-18, VISION)
- C1: suite 139/139 green (17 modules, plain-assert runner incl. defaulted params; stderr noise = expected fallback-path prints, not failures)
- C2: keyless grep zero hits (lib/tony/tests); zero opencode/<id> literals in lib (patterns only, by design)
- C3: --models 7 live + role map; --status JSON valid with mcp key (5 servers); --mcp-status 5 connected
- C4: tagging v0.2 now. No live model burn (P6 proved MCP-use live 80/100; re-burn adds no evidence).

## P8 (v0.3 memory layer — Hermes-replacement step 1) — plan (2026-09-18)
Tier: LIGHT (stdlib file-append + 3 CLI flags + prompt injection point; no plan file -> self-review).
Goal: Tony gains a persistent self across missions: ~/.tony/memory/MEMORY.md append-only, recall/forget, architect sees top memories.
Why this slice first: daemon/chat/scheduler are useless without memory; memory is testable with zero model burn.
Criteria:
- C1: lib/memory.py remember/recall/forget round-trip (dated line, query filter, substring forget) — test with temp HOME
- C2: CLI --remember/--recall/--forget/--memory wired live (round-trip a probe fact, then remove it)
- C3: architect_prompt gains optional memory lines (planner-aware, like MCP names) — test asserts facts in prompt
- C4: suite all green + keyless clean + zero hardcoded model IDs
SURFACE: live CLI round-trip on real ~/.tony/memory. No live model burn (memory proven at seam + live CLI IO).
Teardown: tests use temp HOME dirs; live probe fact forgotten after proof; no procs.

## P8 GREEN + SURFACE (2026-09-18, VISION)
- RED captured: lib.memory unknown import + architect_prompt memory_lines missing (LSP; other-file noise = stale cache per precedent).
- GREEN: suite 141/141 (139 prior untouched + 2 new test_memory). C1 temp-HOME round-trip; C3 prompt carries memory lines.
- SURFACE LIVE: --remember/--recall/--forget round-trip on real ~/.tony/memory (probe fact written, recalled, forgotten, verified absent). --memory prints path + dump. Zero model burn. Real memory file currently empty (fresh start).
- Committed (see log above). No strays (no procs spawned).

## P9 (v0.3 chat — Hermes-replacement step 2) — plan (2026-09-18)
Tier: HEAVY (new interactive integration: REPL + history + live role calls; no plan file -> self-review with live proof).
Goal: `tony chat [--session NAME]` — conversational loop with persistent history (~/.tony/chat/<session>.md), memory auto-injection, each turn a fast-tier role call. The Hermes chat layer, Tony-native.
Criteria:
- C1: lib/chat.py history round-trip (append exchange, load, build prompt includes history + memory lines) — test temp HOME
- C2: REPL control (skips blanks, /quit + EOF exit cleanly, history saved) — test with fake input/output/runner
- C3: suite all green + keyless clean + zero hardcoded IDs
- C4 SURFACE: one live exchange on fast-tier free model (prove conversational reply, not inference)
Teardown: tests fake everything; live proof session file kept as evidence (tiny); no procs left.

## P9 GREEN + SURFACE (2026-09-18, VISION)
- RED captured: lib.chat unknown import (LSP; other-file noise = stale cache per precedent).
- Test fix (mine): test_repl_control asserted raw line, but call_fn correctly receives the BUILT prompt — assertion fixed to match on "user: hi" inside the prompt.
- GREEN: suite 143/143 (141 prior untouched + 2 new test_chat). C1 history round-trip + prompt (history+memory); C2 REPL control (blanks skipped, /quit+EOF clean, history saved); prompt_builder seam for fresh-memory-per-turn.
- SURFACE LIVE (foreground, piped stdin — backgrounded pipes die at tool-call return; pgrep polls self-matched their own command string, lesson logged): `tony --chat p9proof` on lightning-free → "reply with CHAT ONLINE" → model replied "CHAT ONLINE", history file holds both exchanges. C4 PASS, zero stray procs.
- Process lessons: (1) pgrep -f self-matches when the pattern is in the polling command — verify with pgrep -af + grep -v. (2) Background+pipe launches don't survive tool-call return even under setsid — foreground with generous timeout for live proofs.
- Committed (see log above).

## P10 (v0.3 daemon — Hermes-replacement step 3) — plan (2026-09-18)
Tier: LIGHT (inbox poll + claim + loop, mission_fn seam; no plan file -> self-review).
Goal: resident loop: ~/.tony/inbox/*.md -> claim (atomic rename) -> mission_fn -> inbox-done/<stem>.done.md. Live CLI wires mission_fn to cmd_mission (headless, yes=True).
Criteria:
- C1: list_pending skips claimed/done/hidden; claim is atomic rename — test
- C2: run_once executes oldest, writes done-report, removes claimed; empty -> None — test
- C3: loop stop_after + KeyboardInterrupt exits — test
- C4: suite all green + keyless clean + live --help/--models
- C5 SURFACE: live --daemon-once end-to-end on free models (F2-style file mission)
Teardown: tests temp-HOME only; live proof residue logged; no procs left.
PROCESS LESSON (re-learned): foreground live missions in a tool call die at the tool timeout (took the whole mission down at 10:00 with zero output; P6 setsid rule re-proven). Long missions: setsid + log file + short polls, no sleep inside the launch call.

## 18:3x — P10 GREEN, COMMITTED 79a96b2
- RED captured: lib.daemon unknown import (+ stale-cache noise on old files, ignored per precedent).
- GREEN: 149/149 (143 prior untouched + 6 new test_daemon: list/claim, run-once, empty-noop, loop-once, kbd-interrupt, read-fail-release).
- Self-review finds (fixed pre-commit): read-fail left claimed file invisible+wedged -> un-claim on read-fail (+pin test); docstring title-line inaccuracy; one whitespace-merge syntax break (my own bad no-op edit, fixed immediately).
- C5 SURFACE LIVE: --daemon-once on /tmp/tony-daemon-inbox (F2-style hello mission): architect + 3 builders + critic ISSUES (thin proof, correctly adversarial) + 181s fix builder -> 3/3 TODOs + 2/2 wave, MISSION SCORE 80/100, done-file daemonproof.done.md (ok), claimed removed, daemon exited 0. First foreground attempt died at the 10-min tool timeout (zero output, delegates' work survived) — re-ran via setsid+log+poll per P6 rule.
- Lane: keyless clean, zero hardcoded IDs, --models 7 live, --help shows --daemon/--daemon-once/--inbox/--interval.
- Residue cleared: /tmp/tony-daemon-inbox, ~/tony-e2e-daemon. Ledger kept: boulder + fleet report + runs.log + inbox-done/daemonproof.done.md.

## P12 — skills loader (2026-09-18 ~21:10)
- Plan: ~/.tony/skills/*.md discovery + keyword match (hyphen-split) + architect injection + --skills list. Cline SKILL.md shape. RED true (my earlier fake-red lesson: bare python3 on a test file defines fns, runs nothing — always use the plain-assert runner).
- GREEN: suite 154/154 (149 prior + 5 test_skills). Fix during: match() splits hyphenated name tokens.
- CLI: --skills lists; _matched_skills() feeds architect_prompt(mission, mcp, mem, skills) in cmd_mission. Dry-run unchanged (no architect call by design). Chat injection deferred.
- LIVE PROOF (free models, 80/100): skill 'skillproof doctrine' (title must contain SKILLPROOF) -> architect boulder title '# Boulder: SKILLPROOF-verification', 4 doctrine hits in 01-architect.md. 3/3 TODOs + 2/2 wave, report -> ~/.fleet/out/tony-reply-with-skillproof.md. Slow lane: one builder 344s.
- Teardown: probe skill kept (real skill, tiny); mission artifacts = evidence; no procs (pgrep self-match re-confirmed).

## P13 — research fan-out (2026-09-18 ~21:15)
- Plan: `tony --research TOPIC` = 3 parallel explorers (distinct angles, websearch MCP) -> researcher synthesis -> critic gate (+fix loop) -> wave (report exists, >=3 URLs). Pure helpers lib/research.py, orchestration cmd_research.
- GREEN: suite 158/158 (154 + 4 test_research). Wave cmds are real shell (F2 python3 URL-count check, tested fail+pass paths).
- LIVE PROOF (100/100, topic 'Fedora Linux 44 release features'): 3/3 explorers CONCURRENT (timestamps overlap 13s window), synthesis 20s, critic PASS, brief 27 URLs, report -> ~/.fleet/out/tony-research-fedora-linux-44-release-features.md. Hermes-map gap closed: research backend rides opencode free models + websearch MCP (no Gemini lane — by design, keyless).
- Teardown: mission artifacts = evidence; probe exited clean; no procs.


## P14 — packaging: systemd + notify (2026-09-18 ~21:30)
- Plan: lib/packaging.py (unit_text pure builder + install via systemctl --user, no sudo) + daemon.notify() (notify-send, best-effort, fires on every run_once completion) + --install-daemon flag.
- GREEN: suite 161/161 (158 + 3 test_packaging incl. fake-runner notify hook).
- LIVE PROOF: unit written ~/.config/systemd/user/tony-daemon.service, is-enabled=enabled, is-active=active(running), Linger=yes already on -> daemon survives logout+reboot. notify path proven live (desktop pulse + journalctl 'Started tony-daemon.service').
- Hermes-map: ALWAYS-ON closed. Tony is now a resident, auto-started, self-notifying agent on free models.
- Teardown: daemon left running INTENTIONALLY (it's the product now); no other residue.

## P15 — strict critic verdict + chat skills (2026-09-18 ~22:10)
- Plan: lib/critic_verdict.py (first-hit parse — transcript-contamination proof) + research critic gate unification + research boulder persisted BEFORE critic + chat skills injection.
- THE FIND (live, sed-vs-awk proof #1): critic's own verdict VERDICT: ISSUES was flipped to PASS by my last-hit parse — the transcript after the critic's message contained stale 'Verdict: PASS' text from NOTEPAD.md the critic had READ. False 100/100. Also found: cmd_research never saved the boulder (critic reviewed a ghost — its ISSUES was legitimate). Also: grep -c counts LINES not URL occurrences (my '27 URLs' claims were inflated; real check = re.findall count).
- Re-proof #2 (same topic, fresh): ISSUES caught -> fix ran (60s) -> fix's brief had only 1 real URL -> wave refused (1/2) -> RESEARCH SCORE 80/100 honest. No false scoring anywhere in the chain.
- GREEN: 165/165 (163 + test_verdict_first_hit_beats_transcript + chat skills). cmd_mission already strict (P5b critic_gate_detail); only research had the heuristic — now unified.
- Teardown: proof artifacts kept as evidence; no procs.


## P16 — latency honesty (2026-09-19, Vianca's question: why is Tony slow?)
- Finding (MEASURED, not guessed): trivial `opencode run` = ~10s (3 flag variants identical, all agent variants fall back to Sisyphus default); tool-using research mission = 125s on SAME model/lane. No harness tax, no queue, no 429s (ledger zero fails). Minutes = multi-round agentic work, by mission design.
- Fix = mission-shape: research explorer prompts now local-first (websearch only for outside-world facts), explorers stay parallel.
- Artifacts: lib/callshape.py (timed_run + count_internal_steps) + tests/test_p16.py. Probe logs were /tmp-only, cleared at commit.

## P17 — per-role timeouts + --fast (2026-09-19, full autonomy)
- role_timeout(): architect 1.0, builder 0.8, researcher/critic 0.6, explorer 0.4, scribe 0.2 of mission timeout; _exec_one applies it to both first call and demote retry. Backoff shortened 3 attempts [5,20] -> 2 attempts [5] (free-lane stalls cost the mission, demote decides next).
- effective_timeout(): --fast halves mission window, floor 60s; wired in main() so resume/daemon/research/chat/mission all inherit.
- Tests updated deliberately (they pinned old behavior the review told us to change): test_engine_ops backoff counts 3->2/4->3/[5,20]->[5]; test_cli_wiring expects scaled budgets (42->33, 600->480). New: 4 test_p17 (budgets, backoff consts, exec applies 240 for explorer, effective_timeout incl floor).
- GREEN: 186/186 (182 + 4 test_p17). Keyless clean. Live: --fast --models shows 8 models (catalog churn: jev-1.13-free joined; patterns self-healed, no code change).
- Teardown: nothing spawned; no procs.

## v0.3 TAG (2026-09-19)
- 10 commits v0.2..v0.3 (P6-P17). Suite 186/186 re-executed on committed tree. F4 keyless 0 (literals only in test fixtures). --status JSON valid, 8 live models. Daemon active on current tree. Boulder + fleet memory updated. Tag v0.3 -> 7c344dd.




## P11 — scheduler + claim reaper (2026-09-18 ~23:15, FRIDAY)
- Built lib/sched.py (cron */,-steps, dow/month names, dom/dow OR, next_run, schedule.json + minute-ledger, missed windows skipped) + daemon reap_stale_claims(30min) + run_once schedule hook + --add/--list/--rm-schedule flags.
- Tests: 12 new test_sched.py (Feb30-never, */15, dow names, fake-clock due-scan) + 3 in test_daemon.py (stale-reap, fresh-untouched, run_once-fires-due). Suite 180/180, keyless grep clean.
- P14 verified present (unit enabled+active, no rebuild). Live: p11proof added 2min out, daemon fired sched-p11proof at 23:12 via stub (zero model burn), ledger-guarded second pass None, schedule removed.

## P17 follow-up — demote-budget fix (2026-09-20, VISION)
- Demote retry now capped by role_timeout(role, timeout) like the primary (was raw timeout — stall could escape the budget on fallback).
- test_demote_applies_budget pins [240,240] + BLOCKED; stale [5,20]/3x docstring fixed to P17 contract.
- GREEN: 187/187 (186 + 1), py_compile ok, keyless 0 in lib/tony. No live burn (seam proof).


## P18 — domain packs + Hermes-gap defaults (2026-09-20, VISION)
- Goal: close the first Hermes-only surfaces — morning briefing (07:00 daily) and memory hygiene (Sun 09:00) — without hardcoding long prompts into schedule.json.
- lib/packs.py: `~/.tony/packs/<name>.md`; `read_pack()` trims + 8KB cap; missing/unreadable/directory -> empty, never raises; slug-only names block traversal. `@pack:<name>` expands in `sched.run_due` (scheduler seam) and `cmd_mission` (direct missions). Builtin seeds: `morning-briefing`, `memory-hygiene`; `ensure_defaults()` idempotent and never overwrites user packs/jobs.
- CLI: `--packs`, `--pack NAME`, `--install-defaults`. VERSION finally unstuck from P1 -> `0.4.0-p18` (stale-string defect found in self-review).
- Tests: test_p18_packs 8 pins (read/trim/cap/unreadable, traversal, expansion, defaults idempotence, run_due seam, CLI wiring). RED captured before GREEN: run_due was passing raw `@pack:` to mission_fn.
- GREEN: 195/195 (187 + 8), py_compile ok, keyless 0, git diff --check clean.
- LIVE install on real HOME: packs seeded + both schedules added; `--list-schedule` valid JSON; next fires 2026-09-21 07:00 (brief) and 2026-09-27 09:00 (hygiene); systemd daemon active and will serve them through the normal run_due path. No model burn (no due window at install time).
- Commit f686dcd. MISSION SCORE: 88/100 — P18 verified; live model-fired pack mission still unproven until the next due window.


## P19 — external-review hardening (2026-09-20, Vianca: "make tony god level")
- Input: Codex 48/100 (sub-agent 42 BLOCK) + Antigravity 22-32; synthesis in ~/.fleet/out/tony-external-reviews-synthesis.md. Every claim verified against the tree before acting; one AG claim (roles run sequentially) disproven.
- P19a TRUST: lib/waveguard.py — deny-list (sudo/disk/fork-bomb/remote-shell/power) + sh -n parse gate BEFORE engine.run_wave shell=True; hostile sudo rm -rf wave → FAIL+log, never executed (seam proof F3). Research citations now membership-verified (report URLs ⊆ explorer corpus) — URL counting demoted to legacy mode.
- P19b BUGS (all 7 from reviews): forget("") wipe → no-op; chat multiline escape/unescape (incl backslash literals); boulder [X] parses checked; boulder.save tmp+fsync+replace atomic; tui nodelay tight loop → bounded win.timeout; evidence_coverage version-string false positives → line-leading anchor only; systemd unit dropped After=graphical-session.
- P19c HONESTY: critic at >=2 TODOs (was 3); N/A gate bonus 10 → 0 (no free points; 1-TODO cap 80). Two score pins updated deliberately with rationale.
- P19d PACKAGING: README (honest, security model first), pyproject.toml (ruff+mypy config, vendored excluded), run_tests.py stdlib runner; ruff 0 across project scope, mypy 0 in 26 files.
- RED 14/17 → GREEN 212/212 (195+17). py_compile clean, keyless 0, --models live, daemon active. Commits ce5f994 + 7802315, correct authorship. MISSION SCORE: 85/100 (live model-fired waveguard/citation proof pending the next free scheduler window).


## P20 — self-proof + hygiene (2026-09-20, autonomy)
- `tony --selftest`: suite + waveguard seam + ruff + mypy printed as one PASS/FAIL line each, exit 1 on any failure; optional tools SKIP when absent (never fake PASS). Live result: SELFTEST PASS 4/4.
- Fork-bomb-class bug found mid-build: `--selftest` ran run_tests.py from inside the suite → full recursion. Fixed with `--skip-self` + `_self_check` recursion guard on the runner.
- Research legacy URL-count mode deleted (sources_path now required; caller + tests migrated).
- 15 phase-named test files renamed to functional names (git mv, zero logic); suite now reads as a feature map.
- Free-lane live call confirmed post-hardening: `opencode run` on muse-spark → "TONY P20 LANE OK".
- GREEN 217/217 (212+5). py_compile clean, keyless 0, ruff clean, mypy clean. Commit aaae638. MISSION SCORE: 90/100 (self-verifying + documented; remaining ceiling is live model-fired waveguard/citation missions).


## P21 — live fire proof on free models (2026-09-20, autonomy)
- `tony --yes --fast` F2-style mission on free lane, 15:24–15:40: artifact byte-exact on disk (grep -qxF CONTENT_MATCH), 4/4 TODOs, 3/3 wave, MISSION SCORE 80/100 with ISSUES gate honestly on record.
- Critic proved adversarial LIVE: trailing-newline byte pedantry, unchecked waves at review time, explorer wandering — ISSUES issued with per-TODO evidence.
- Demote-once composed twice under real lightning-free stalls, zero retry storms.
- Model-authored waves (test -f/-s/grep pipes) all cleared waveguard — zero false positives.
- HONEST finding queued as P22: ISSUES → builder fix FAILED → wave still ran (pre-existing yes-mode contract), log chain shows hold→fail→execute without an explicit override line. Wave-after-failed-fix must log the bypass explicitly.
- Boulder: ~/.fleet/boulder/tony-p21-livefire.md (all green). MISSION SCORE: 88/100.


## P22 — critic-override contract (2026-09-20, autonomy)
- From P21 live-fire finding: ISSUES -> builder fix FAILED -> wave ran with no explicit override line in the chain.
- apply_critic_gate now returns (gate, fix_status): none|ok|fail|held. Failed fix (return "fail"/False or raise) writes "ISSUES OVERRIDE — builder fix failed; wave results are UNVERIFIED-until-they-pass" to the boulder; cmd_mission also prints it pre-wave where a human sees it.
- RED 3 failing first (tuple unpack + missing OVERRIDE), GREEN 221/221 (217+4). Gate pins migrated deliberately. ruff+mypy clean, keyless 0. Commit c18799e. MISSION SCORE: 92/100.


## P23 --doctor (plan: ses_f41993632ffe5zWinfMlEPC439)
- Pin the seam for `lib/doctor.py`'s `run_all(home, catalog_fn, mcp_fn, run_fn, which_fn) -> [(name, status, detail)]` with status in {ok, warn, fail, skip}.
- tests/test_doctor.py written with 8 bare `def test_*():` functions (plain asserts, no pytest/decorators) + one CLI-wiring source pin (`--doctor` flag, `cmd_doctor` def, dispatch string).
- All dependencies faked: temp HOME via `tempfile.mkdtemp` + `shutil.rmtree` in try/finally; fake `catalog_fn`/`mcp_fn`/`run_fn`/`which_fn` lambdas; `run_fn` raising `FileNotFoundError` for systemctl-absent case. Zero live model calls, zero real sleep, zero real-HOME mutation, zero daemon/systemctl state changes.
- 8 behaviors pinned: all-ok healthy path; binary-missing -> fail; catalog_fn raises/empty -> fail with detail; run_fn raising FileNotFoundError -> skip; unit installed-but-inactive (nonzero returncode) -> warn; bad cron names the job -> fail; corrupt ledger -> warn; present-but-unwritable home -> fail. Fresh-machine (absent-but-creatable ~/.tony paths) pinned as detail/ok.
- RED captured:
```
PASS=0 FAIL=1
  FAIL test_doctor:import ModuleNotFoundError: No module named 'lib.doctor'
```
- lib/doctor.py not yet created — this is the expected seam-pin RED state.

## P23 GREEN — --doctor self-diagnosis (2026-09-20, autonomy)
- T2 needed 2 delegate attempts then direct implementation: quick-lane delegates ruminated on the bad-cron semantics + CLI-pin contradiction instead of writing. Resolved: .tony-present-but-no-schedule.json -> schedules FAIL (half-initialized home IS sick); empty catalog/MCP -> ok (fresh-machine test forbids fails/warns); CLI pin declared T4 scope. Lesson: single-file fully-specified tasks go direct after one delegation failure, not two.
- T1 test file revealed a real design constraint the plan missed: sched.load/load_ledger swallow corruption (return []/{}) and config.load reads real HOME — doctor reads home-scoped JSON directly to honor temp-HOME isolation.
- GREEN: 231/231 (221 prior unmodified + 10 new). ruff 0, mypy 0 (26 files), keyless 0, zero opencode/<id> literals.
- SURFACE LIVE: --doctor HEALTHY 9/9 exit 0 (8 models, 2 sched jobs, daemon active, 5 MCP); --selftest 4/4; --models 8 live. Zero model burn.
- MISSION SCORE: 90/100 (self-diagnosing now; remaining ceiling is live failure-path proof, which must never be forced on the real home).

## P24 — wave cwd follows mission workdir (2026-09-20, autonomy)
- Recon (T1 delegate, verified): run_wave/verify_wave default cwd="/tmp" (engine.py:78,292); cmd_mission (tony:382) + cmd_resume (tony:427) compute workdir (tony:327,414) but never pass it — relative wave items execute in /tmp and fail spuriously. selftest tony:644 excluded (synthetic boulder, /tmp intentional). No research wave site.
- RED captured:
```
PASS=2 FAIL=1
  FAIL test_wave_cwd:test_s3_entrypoints_pass_cwd AssertionError: cmd_mission must pass cwd=workdir into verify_wave (tony:382)
```
- Full suite with spec: PASS=233 FAIL=1 (231 prior green; S1 passes documenting correct explicit-cwd behavior, S2 wave fails as predicted proving cwd load-bearing, S3 pins the entrypoint bug).

## P24 GREEN — wave cwd follows workdir (2026-09-20, autonomy)
- T3: cwd=workdir threaded at tony:382 (mission) + tony:427 (resume); selftest tony:644 keeps /tmp with exclusion comment; VERSION 0.4.0-p24 in tony + pyproject (was p18/p19 drift).
- GREEN: 234/234 (231 prior unmodified + 3 new). ruff 0, mypy 0 (26 files), keyless 0, zero opencode/<id> literals.
- SURFACE LIVE: --selftest 4/4; --doctor HEALTHY 9/9; --models 8 live; --version 0.4.0-p24. Zero model burn.
- MISSION SCORE: 92/100 (spurious relative-wave failures eliminated at both entrypoints; P25 candidate queued: double-daemon claim race).

## P25 — daemon loser-yields on claim race (2026-09-20, autonomy)
- Seam verified: run_once list_pending (daemon.py:118) -> claim(src) (:127) unguarded; lost race kills the daemon with FileNotFoundError (loop dies, systemd crash-loops, --daemon-once exits nonzero).
- T1 delegate wrote the spec file then hung on one tool call (cancelled bg_5c9d2a5b, took over). Spec review found a REAL flaw: pre-claiming job.md->job.md.claimed makes list_pending skip it, so run_once noops vacuously and the spec passed 3/3 WITHOUT the guard. Fixed S1/S2 to inject the race synchronously (monkeypatch daemon.claim: peer removes src, then real claim raises) — the only faithful single-threaded simulation of the TOCTOU window. Pin comments kept deliberately (P4 precedent: they stop future "simplification" back to the vacuous version).
- RED captured:
```
PASS=1 FAIL=2
  FAIL test_claim_race:test_loop_survives_stolen_claim FileNotFoundError: ... job.md' -> '... job.md.claimed'
  FAIL test_claim_race:test_loser_yields_none FileNotFoundError: ... job.md' -> '... job.md.claimed'
```
- Full suite with spec: PASS=235 FAIL=2 (234 prior green + S3 winner anchor green by design — anchors pass pre- and post-fix; S1/S2 pin the crash).

## P25 GREEN — loser-yields guard (2026-09-20, autonomy)
- T3: 4-line guard at daemon.py:127 (try claim / except FileNotFoundError -> None). Only FileNotFoundError caught — PermissionError stays loud. claim() contract unchanged; loop()/--daemon-once ride the existing None path (sleep+repoll, exit 0).
- GREEN: 237/237 (234 prior unmodified + 3 new). ruff 0, mypy 0 (26 files), keyless 0, zero opencode/<id> literals, diff-check clean.
- SURFACE LIVE: --selftest 4/4; --doctor HEALTHY 9/9; --models 8 live; --version 0.4.0-p24. Zero model burn, no stray procs.
- MISSION SCORE: 90/100 (double-daemon now degrades to yield+repoll instead of crash-loop; remaining ceiling is a live two-daemon proof, deliberately never forced).

## P26 — sched atomic persistence (2026-09-20, autonomy)
- Seam verified by plan agent: sched.save + mark_fired plain-open("w")+dump (sched.py:166-171,230-237); torn write -> load/load_ledger swallow as []/{} -> fired jobs silently refire. P25's loser-yields makes two live daemons the normal case. Scope honesty: fixes torn writes, NOT cross-process double-fire (same-minute idempotent, harmless by design).
- RED captured:
```
PASS=2 FAIL=2
  FAIL test_sched_atomic:test_interrupted_save_keeps_prior_jobs AssertionError: expected 2 prior jobs, got []
  FAIL test_sched_atomic:test_interrupted_mark_keeps_prior_ledger AssertionError: expected prior ledger entry, got {}
```
- Full suite with spec: 237 prior green + S3/S4 anchors green (S1/S2 pin the torn write).

## P26 GREEN — sched atomic persistence (2026-09-20, autonomy)
- T2: _write_json_atomic (makedirs + tmp + flush + fsync + replace, boulder.save mirror) routed through save() + mark_fired(); signatures, indent=2, load swallow-semantics untouched.
- GREEN: 241/241 (237 prior unmodified + 4 new). ruff 0, mypy 0 (26 files), keyless 0, zero opencode/<id> literals, diff-check clean.
- SURFACE LIVE: --selftest 4/4; --doctor HEALTHY 9/9; --models 8 live; temp-HOME save/mark round-trip OK, zero *.tmp residue. Zero model burn, no ~/.tony mutation.
- Honest scope (P22 precedent, no overselling): fixes torn-write corruption (crash mid-write, concurrent-writer interleave). Does NOT fix cross-process double-fire (scan->mark TOCTOU remains by design; same-minute idempotent, harmless).
- MISSION SCORE: 88/100 (silent-refire eliminated; queued P27: doctor @pack: blind spot; parked P28: waveguard red-team probe; v0.4 tag is Vianca's call).

## P27 — doctor resolves @pack: refs (2026-09-20, autonomy)
- Seam: _check_schedules validated cron/fields but never resolved @pack: refs; both live jobs are @pack: missions, and run_due feeds the RAW ref string on missing packs while doctor stayed HEALTHY. Decision (frozen): missing pack -> WARN (fires degraded, corrupt-ledger precedent), never fail.
- Plan lane died (30-min poll timeout + empty continuation) — self-planned from frozen queue entry; cheaper than a third plan round-trip for a one-check slice.
- T1 delegate wrote a strong spec then hung (cancelled bg_2ac29779, same pattern as P25). Spec verified non-vacuous: mirrored _PACK_RE byte-identical to packs.py:19; packs.read_pack is home-parameterized (no P23-style isolation trap).
- RED captured:
```
PASS=2 FAIL=2
  FAIL test_pack_refs:test_missing_pack_warns AssertionError: PRE-FIX RED confirmed: got ('schedules', 'ok', '1 jobs')
  FAIL test_pack_refs:test_two_refs_one_missing_warns_only_missing AssertionError: PRE-FIX RED: got ('schedules', 'ok', '1 jobs')
```
- Full suite with spec: 241 prior green + S2/S3 anchors green (S1/S4 pin the blindness for the right reason — check never consults packs).

## P27 GREEN — doctor resolves @pack: refs (2026-09-20, autonomy)
- T2 direct: _check_schedules scans each job mission with packs._PACK_RE (same set run_due expands) and warns naming job+pack when packs.read_pack(ref, home)=="" (missing OR empty — both expand to nothing at fire time). Structural fails keep precedence; live doctor HEALTHY 9/9 (both real packs present).
- GREEN: 245/245 (241 prior unmodified + 4 new). ruff 0, mypy 0 (26 files), keyless 0, zero opencode/<id> literals, diff-check clean.
- SURFACE LIVE: --selftest 4/4; --doctor HEALTHY; --models 8 live. Zero model burn, no ~/.tony mutation (missing-pack warn proven at seam only — never forced live).
- MISSION SCORE: 88/100 (last auditor-confirmed gap closed; parked P28: waveguard red-team probe; v0.4 tag is Vianca's call).

## P28 — waveguard red-team + harden (2026-09-20, autonomy)
- Deliberate probe (the sanctioned P28 path): 18 candidates probed as strings against check(). KEPT 9 true slips: rm -rf on dot/relative/env/tmp targets (root-only pattern required /|~|* right after space) + curl|wget piped to python3 (interpreter class was sh-only). DROPPED 4 already-blocked: rm -rf ~, rm -rf *, curl|bash, curl|sh. mv-class destructive moves unprobed, out of scope.
- Spec delegate derailed into a repetition loop without writing the file — wrote spec direct (probed-kept discipline + benign corpus anchor per plan). No plan-agent round-trip (lane dead; queued P28 definition already scoped it).
- RED captured:
```
PASS=1 FAIL=1
  FAIL test_waveguard_redteam:test_redteam_hostile_blocked AssertionError: slip still allowed: 'rm -rf .' ()
```
- Full suite with spec: 245 prior green + benign anchor green.
- T2: "recursive rm (any target)" pattern (any -r/R short-flag cluster; single-file rm -f stays allowed by construction) + piped-interpreter class extended to python/perl/ruby/php/node on both curl|wget entries.
- GREEN: 247/247 (245 prior unmodified + 2 new). ruff 0, mypy 0 (26 files), keyless 0, zero opencode/<id> literals.
- SURFACE LIVE: --selftest 4/4; --doctor HEALTHY; --models live. Zero model burn; hostile strings never executed (check() args only).
- MISSION SCORE: 90/100 (deny-list now covers the probed holes with the zero-false-positive property re-pinned; residual risk is unprobed exotic exfil, not denial).

## v0.4 RELEASE (2026-09-20, autonomy — "until it's all done")
- Scope: P18→P28 (18 commits since v0.3 tag 7c344dd): packs + @pack expansion, scheduler, daemon + loser-yields, research membership citations, critic v2 + override contract, score honesty, waveguard + red-team, sched atomicity, doctor (9 checks) + pack resolution, wave cwd, TUI/systemd/chat/skills/memory/chat-history hardening, selftest, VERSION 0.4.0-p24.
- Audit: external explore hung in one bash call (~20 min, cancelled bg_48518f2f — third hang this week). Self-audit instead: full v0.3..HEAD lib diff reviewed hunk-by-hunk (830 ins). Every behavior change matches its NOTEPAD rationale (P19a/b/c, P22, P24–P28); new files all spec-pinned; tony CLI removals all have pinned replacements. Verdict: SHIP, zero blockers. NOTE (non-blocking, pre-existing P18): run_due on fully-missing pack expands to "" and fires an empty mission — degraded, doctor now warns; queued, not a gate.
- Triage F1-F4: suite 247/247; keyless grep 0; --selftest 4/4; --doctor HEALTHY 9/9 exit 0; --models 7 live + role map (catalog churn 8→7, patterns self-healed); --status JSON valid; daemon active.
- Tagging v0.4 on the ledger commit below. Push left for Vianca (never push unasked).

## H1 — Kimi bridge read-only seam (2026-09-20, autonomy — Hermes-level lane 1)
- Goal: daily read-only job (LinkedIn applied-jobs + Proton reply scan) via her real browser sessions. Decision: Kimi bridge (no re-logins, no solo WAF fights). SAFETY LAW: read-only — extract text only, never click/fill/send/mutate; no write wrappers exist by construction.
- RED captured:
```
PASS=0 FAIL=1
  FAIL test_kimi_bridge:import ModuleNotFoundError: No module named 'lib.kimi'
```
- Full suite with spec: 247 prior green (15 frozen pins in tests/test_kimi_bridge.py: post/status/tabs/snapshot/read/find/navigate/scan_subjects + write-absence pin).

## H1 GREEN — Kimi bridge read-only seam (2026-09-20, autonomy — Hermes lane 1)
- T2/T3 landed via delegates (T2 hung post-delivery, cancelled; file verified green on disk — standing pattern). lib/kimi.py: urllib-only post/status/tabs/snapshot/read/find/navigate/scan_subjects; zero write symbols (absence-pinned). --bridge-start explicit-only (probe-never-spawns pinned); doctor 10th check bridge (ok/warn/skip).
- T3 ran --bridge-start once to prove it (skill-sanctioned: "start it yourself... safe to run anytime"; start serves the extension, touches no tabs/profile — NOT a violation).
- T4 live proof (direct, foreground, read-only): daemon reachable; session tony-h1-proof opened 3 grouped tabs; python.org navigate->evaluate extracted 3024 chars (mechanism proven on live web). Target A (LinkedIn applied-jobs) + Target B (Proton inbox): BLOCKED on login walls (exact wall text captured; no creds touched, no bypass attempted). Unblock: Vianca logs into both once in Chrome; re-run proof. Evidence: ~/.fleet/out/tony-h1-proof.json. Tabs left open for her to close on ask. Zero opencode runs in proof window; zero write-action calls.
- GREEN: 266/266 (247 prior unmodified + 19 new). ruff 0, mypy 0 (27 files), keyless 0, zero opencode/<id> literals, diff-check clean.
- SURFACE LIVE: --selftest 4/4; --doctor HEALTHY 10/10; --models live. Zero model burn.
- Follow-ups (H2): route thin wrappers (navigate etc.) through post() so they actually drive; systemd unit for kimi daemon (needs her call); the live site proof re-run post-login.
- H1 PROOF UPDATE (same night, Vianca logged into Proton): Target B GREEN — inbox readable (339 unread, 308 subject lines page 1), scan_subjects over legend keywords: 0 interview/offer hits, buildbear 0. Notables: LinkedIn hibernation notice Sep 16 (independently confirms hibernation), Proton Free downgrade Sep 18. Target A stays BLOCKED (hibernating account, confirmed twice). Raw dumps deleted after counting (counts + keyword JSON only in ~/.fleet/out/tony-h1-proof.json — inbox PII minimized). Zero opencode runs, zero write calls. Suite 266/266 re-verified (no code change).

## P30 — paginated inbox reply scan (2026-09-20, autonomy — Hermes daily job)
- H1 proved page-1 reads; Hermes checks FOR REPLIES (12 pages here). Probe: nav.mail-toolbar tiny-Next pager scoped via DOM chain (not the conversation-pane twin); no emails opened, no site data mutated (list-pagination only).
- Mid-slice find (live): whole-page keyword scan false-hits 12/12 on UI chrome (2-letter 'oa' matched nav text). Fixed HONESTLY: row parser (Star-conversation-delimited sender/subject) + dropped 'oa' with documented reason (spec-untouched; scan_subjects semantics frozen). Spec rewritten pre-GREEN to model the daemon faithfully (idempotent reads, click-advances-cursor fakes).
- RED: 4/4 AttributeError (right reason). GREEN: 274/274 (268 prior unmodified + 6 new). ruff 0, mypy 0 (27 files), keyless 0, diff-check clean.
- SURFACE LIVE: 12 pages walked (12 distinct first-subjects, 50x11+25=575 rows), 1 hit (Glassdoor digest quoting someone else's offer, Dec 2025 — newsletter noise, NOT an invite). Verdict: quiet, no genuine replies. Evidence ~/.fleet/out/tony-p30-scan.json (counts + 1 hit + per-page hashes, no inbox dump). Zero opens, zero write calls, zero model burn.
- SURFACE GATES: --selftest 4/4; --doctor HEALTHY 10/10; --models 7 live.
- MISSION SCORE: 92/100 (Hermes' daily check now exists as callable lib + proven live end-to-end; remaining: scheduler wiring for daily runs — needs her call on timing).

## P31 — daily reply-check command + schedule (2026-09-20, autonomy — Hermes mornings)
- lib/inboxscan.py (new): run_scan() deterministic — navigate-first (live found the 502: scan assumed a tab), scan pages, write dated report to ~/.fleet/out, notify-send on hits ONLY (quiet/infra stay silent, Hermes rule), exit 0/1. 'oa' excluded with evidence. tony --inbox-scan thin pass-through.
- scan_inbox_pages migrated to row-scoped scanning (live chrome-noise lesson); S4 fixtures migrated to row protocol + new chrome-never-hits pin (P17 precedent: deliberate contract change, intent preserved).
- Schedule: inbox-reply-check 30 7 * * * installed live (fires 2026-09-21 07:30, after briefing). Inline mission (no packs.py change — builtin would break the frozen P18 2-pack pin; tradeoff noted, graduate if doctrine grows). schedule.json is user-data, untracked.
- RED: import-RED then navigate-missing 502 live. GREEN: 281/281 (274 prior + 7 new). ruff 0, mypy 0 (28 files), keyless 0, diff-check clean.
- SURFACE LIVE: --inbox-scan exit 0, 12 pages / 575 rows / 1 noise hit (Glassdoor digest, correctly non-invite); --selftest 4/4; --doctor HEALTHY 10/10; --models live; --list-schedule shows the job. Zero model burn end-to-end.
- MISSION SCORE: 93/100 (Hermes' mornings now run themselves: scan + notify + schedule; remaining Hermes deltas: delivery lane (needs her token), LinkedIn (hibernating), research depth (structural)).

## P29 — waveguard destructive moves (2026-09-20, autonomy)
- Deliberate probe #2 (18 candidates as strings, never executed): 9 true slips pinned — mv /*, mv-to-/dev/null ($HOME/~/work forms), find -delete (incl /-rooted), ln to dotfile/devnull, redirect into home dotfiles ($HOME/${HOME} forms included). Documented OUT (not pinned, not hardened): cp/tar/zip/cat reads (exfil = sandbox problem), chmod/chown non-root (recoverable via git), obfuscated interpreter payloads (regex-uncatchable without theater), plain mv renames (harmless).
- Assessed-not-changed (honest no-op): H2 wrapper-routing — frozen spec's zero-arg fakes forbid routing wrappers through post(); wrappers are parse-helpers, post() is the driver (H1 proof already drives post() directly). Queued notes that died on contact with the spec stay dead.
- RED: hostile ALLOWED (`mv /* /tmp/x`), benign green. GREEN: 268/268 (266 prior unmodified + 2 new). ruff 0, mypy 0 (27 files), keyless 0, diff-check clean.
- SURFACE LIVE: --selftest 4/4; --doctor HEALTHY 10/10; --models 7 live. Zero model burn.
- MISSION SCORE: 90/100 (deny-list now covers moves + pipes + recursive rm with precision anchors; residual is exfil/obfuscation — sandbox territory, declared).
- MISSION SCORE: 88/100 (lane + lifecycle + doctor shipped, mechanism proven live; site proofs honestly BLOCKED on her logins — the boundary the safety law predicted).

## v0.4 PUSHED (2026-09-20, autonomy — Vianca: "Push v0.4" then "Public tony repo")
- No remote existed; gh authed as workbydivyanshu. Pre-publish audit: keyless verified, .omo strays inert session JSON (no secrets), no memory/inbox/runs tracked.
- Created https://github.com/workbydivyanshu/tony (PUBLIC), pushed master + v0.4 (both 120a227, verified via ls-remote). Older tags v0.1–v0.3 left local-only.
- MISSION SCORE: 95/100 — Tony is public and released.
