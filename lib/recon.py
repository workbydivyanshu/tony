"""recon.py — pre-architect explorer pass (P37 Cline rung). Stdlib only.

Judgment mechanized as groundedness: before the architect writes the
boulder, explorers map the target repo and their findings ride into the
architect prompt. Pure orchestration over an injected role_call_fn —
no subprocess, no models, no disk. A blowing explorer yields nothing
for its slot; recon never kills the mission it serves.
"""
ANGLES = (
    "map the directory layout under {workdir} for this mission "
    "({mission}): top-level dirs, entry points, where code vs tests "
    "vs docs live. Be concrete (paths). Report only — change nothing.",
    "find the files under {workdir} most relevant to this mission "
    "({mission}): paths plus one line on why each matters. Report "
    "only — change nothing.",
    "note conventions, risks and traps for this mission ({mission}) "
    "under {workdir}: build/test commands, generated files, things "
    "that must not be touched. Report only — change nothing.",
)


def run_recon_phase(role_call_fn, explorer_model, workdir, mission,
                    angles: int = 3) -> list:
    """Run up to `angles` explorer calls, collect findings in order.

    role_call_fn(role, subtask) is injected (live: bound eng.role_call
    with the explorer model + workdir). explorer_model is accepted for
    introspection/logging symmetry and ignored by the phase itself.
    """
    _ = explorer_model
    findings: list = []
    for template in list(ANGLES)[:max(0, min(angles, len(ANGLES)))]:
        prompt = template.format(workdir=workdir, mission=mission)
        try:
            findings.append(role_call_fn("explorer", prompt))
        except Exception:
            continue
    return findings
