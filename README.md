# Tony

A **free-model-native agent CLI** that turns `opencode run` into a disciplined,
multi-role engineering harness — stdlib-only Python, zero pip dependencies,
zero API keys, zero cost per run.

Tony is **not** a general chat agent and not a peer of Cline/OpenCode/Hermes.
It is a small, sharp orchestrator with one thesis: **an agent mission is a
boulder (plan → execute → verify → score), not a chat transcript.**

## Quickstart

```bash
./tony --models                 # live free-model catalog + role assignments
./tony --status                 # JSON: catalog, tiers, roles, MCP, boulders
./tony "create ~/tmp/hello.txt containing HELLO, then verify"   # one-shot mission
./tony --research "topic"       # 3-way explorer fan-out → cited brief → critic
./tony --chat                   # REPL with persistent history + memory
```

The model layer is always `opencode run --model <model> <prompt>` — never raw
HTTP — so whatever free catalog OpenCode exposes, Tony rides it. Model IDs are
discovered live from `opencode models` and pattern-matched to roles; nothing
is hardcoded.

## The mission loop

1. **Architect** turns the mission into a boulder: 3–7 TODOs with
   `[role:builder|explorer|researcher]` tags + a Final Verification Wave of
   shell commands.
2. **Plan gate** (TTY: y/N; headless: `--yes`) before any builder burns tokens.
3. **Builders/explorers** execute TODOs; explorers run in parallel threads.
   Model failure → demote once within tier → `[BLOCKED]`, no retry storms.
4. **Critic** (mandatory at ≥2 TODOs) must emit `VERDICT: PASS|ISSUES`;
   ISSUES triggers one bounded builder fix.
5. **Wave guard** parses every verification command (`sh -n`) and denies
   destructive patterns before `shell=True` ever sees it.
6. **Score**: `40×TODO + 40×wave + 20×critic`, hard-capped (blocked ≤ 49,
   no wave ≤ 40, no critic = 0 bonus). Scores are earned, never granted.

## Surface

| Area | Entry |
|------|-------|
| Missions | `tony "mission" [--parallel] [--yes] [--fast] [--timeout N]` |
| Resume/watch | `--resume SLUG`, `--watch SLUG`, `--tui SLUG` |
| Research | `--research TOPIC` (citations verified by membership against explorer corpus) |
| Daemon | `--daemon [--inbox PATH]` + `--install-daemon` (systemd user unit) |
| Scheduler | `--add-schedule "name :: cron :: mission"`, `--list-schedule` |
| Domain packs | `--packs`, `--pack NAME`, `@pack:name` refs expand to ≤8KB payloads |
| Defaults | `--install-defaults` seeds morning-briefing (07:00) + memory-hygiene (Sun 09:00) |
| Memory | `--remember/--recall/--forget/--memory` |
| Skills | `--skills` (keyword-matched `.md` doctrine injected into the architect) |
| Chat | `--chat [SESSION]` |
| Doctor | `--doctor` (self-diagnose: binary, catalog, roles, config, daemon, schedules, paths, MCP) |

Everything lives under `~/.tony/` (boulders, memory, packs, schedule,
inbox, work dirs, runs.log). Reports land in `~/.fleet/out/`.

## Security model (read this)

- **Wave commands come from a model.** Tony gates them with `lib/waveguard.py`
  (deny-list: sudo, disk writes, fork bombs, piped remote shells, power ops;
  plus `sh -n` syntax validation) — a blocked command fails its wave item and
  is never executed. This is a guard rail, not a sandbox: only run missions
  you authored or reviewed.
- Research citation checks verify **membership**: every URL cited in the brief
  must have appeared in an explorer output. Invented URLs fail the wave.
- `--yes` bypasses the plan gate — use it for daemon/headless only.

## Tests

```bash
python3 run_tests.py            # full suite, plain-assert, stdlib only
python3 run_tests.py tests/test_p19.py
```

No pytest/pluggy needed. `ruff check` and `mypy` are configured in
`pyproject.toml` (vendored comparison repos are excluded from both).

## Honesty section

Tony was built in days as a personal harness, not a product. Known limits:
it is coupled to the `opencode` binary by design (that IS the free-model
lane), has no browser/computer-use, no messaging integrations, and no
self-learning loop. The boulder/scoring discipline is the contribution; the
rest is scaffolding around it.
