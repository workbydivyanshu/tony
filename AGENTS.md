# Tony — agent working rules (read before touching this repo)

## Branch + review law (Vianca's standing order, 2026-09-21)

- **Whichever AI works here pushes to a BRANCH, never master.** Branch shape:
  `work/<slug>` (e.g. `work/p34-x`, `work/h2-wrappers`). One slice, one branch.
- **Master advances only by reviewed merge.** Vianca reviews the branch
  (diff + suite evidence in NOTEPAD), then merges (`--no-ff`) and pushes
  master herself. No agent merges to master. No agent pushes master.
- **Why:** off-device copies are the restore path (a 02:40 bulk tree
  rewrite proved local-only work can vanish). No device-only state:
  every landed slice must exist on GitHub the same night.
- Tags (`v*`) are Vianca's call. Never tag, never push tags.

## Authorship law (absolute — violated once, cost a filter-branch)

- Commits: `workbydivyanshu <lifeofdivyu@proton.me>`, no trailers,
  no co-authors, message shape `tony: <P/T/H-NN> <what> (<pass>/<pass>)`.
- One atomic commit per verified slice. Never amend pushed work.

## Build law (short version — full contract in NOTEPAD.md tail)

- Test-first, RED must name the missing behavior, frozen specs are never
  edited to green. `python3 run_tests.py` + `ruff` + `mypy` + keyless
  grep green before every commit. Zero live model burn in the suite.
- Read-only means read-only: no git/archive/tar/cp/restore commands in
  exploratory agents. Verify `git status` clean after every delegation.
