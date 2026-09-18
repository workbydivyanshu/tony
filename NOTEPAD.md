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
## Todo
- test_boulder.py RED
- lib/boulder.py GREEN
- lib/roles.py architect template
- tony --dry-run wired + live verify C1/C2/C3
- commit + notepad
