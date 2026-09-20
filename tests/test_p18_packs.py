"""tests/test_p18_packs.py — P18 packs loader (read_pack, packs_dir)."""
import sys, os, tempfile, shutil
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_read_pack_missing_empty():
    """Missing pack file returns empty string, never raises."""
    from lib import packs
    d = tempfile.mkdtemp()
    try:
        result = packs.read_pack("nonexistent", d)
        assert result == "", result
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_read_pack_trims_and_returns():
    """Read pack strips whitespace and caps at ~8KB."""
    from lib import packs
    d = tempfile.mkdtemp()
    try:
        pd = packs.packs_dir(d)
        os.makedirs(pd, exist_ok=True)
        with open(os.path.join(pd, "alpha.md"), "w") as f:
            f.write("  hello pack  \n")
        result = packs.read_pack("alpha", d)
        assert result == "hello pack", repr(result)

        # cap at ~8KB: write 12KB, expect truncated to 8192
        with open(os.path.join(pd, "big.md"), "w") as f:
            f.write("x" * 12000)
        result = packs.read_pack("big", d)
        assert len(result) <= 8192, len(result)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_read_pack_unreadable_empty():
    """Unreadable or directory pack returns empty string, never raises."""
    from lib import packs
    d = tempfile.mkdtemp()
    try:
        pd = packs.packs_dir(d)
        os.makedirs(pd, exist_ok=True)
        # directory instead of file (must use .md suffix to match pack path)
        os.makedirs(os.path.join(pd, "dirpack.md"), exist_ok=True)
        result = packs.read_pack("dirpack", d)
        assert result == "", repr(result)

        # unreadable file (no read perms)
        bad = os.path.join(pd, "noperm.md")
        with open(bad, "w") as f:
            f.write("secret")
        os.chmod(bad, 0o000)
        result = packs.read_pack("noperm", d)
        assert result == "", repr(result)
        os.chmod(bad, 0o644)  # restore for cleanup
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_expand_replaces_pack_refs_and_leaves_plain_text():
    """@pack:name -> body; missing pack -> removed; plain mission untouched."""
    from lib import packs
    d = tempfile.mkdtemp()
    try:
        pd = packs.packs_dir(d)
        os.makedirs(pd, exist_ok=True)
        with open(os.path.join(pd, "alpha.md"), "w") as f:
            f.write("PAYLOAD BODY")
        assert packs.expand("Do X @pack:alpha now", d) == "Do X PAYLOAD BODY now"
        assert packs.expand("Do X @pack:ghost now", d) == "Do X  now"
        assert packs.expand("plain mission", d) == "plain mission"
        assert not packs.has_pack_ref("plain mission")
        assert packs.has_pack_ref("@pack:alpha")
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_expand_refuses_traversal_names():
    """@pack:../secret and absolute-ish refs must never read outside packs/."""
    from lib import packs
    d = tempfile.mkdtemp()
    try:
        # a readable file OUTSIDE packs/: must stay unreachable
        outside = os.path.join(d, "secret.md")
        with open(outside, "w") as f:
            f.write("SECRET")
        text = "read @pack:../secret please"
        assert "SECRET" not in packs.expand(text, d)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_ensure_defaults_seeds_idempotently():
    """ensure_defaults: creates 2 builtin packs + 2 cron jobs; second call
    creates nothing; existing user job/pack never overwritten."""
    from lib import packs
    d = tempfile.mkdtemp()
    try:
        first = packs.ensure_defaults(d)
        assert sorted(first["packs"]) == ["memory-hygiene", "morning-briefing"], first
        assert sorted(first["jobs"]) == ["memory-hygiene", "morning-briefing"], first

        from lib import sched
        jobs = {j["name"]: j for j in sched.load(d)}
        assert jobs["morning-briefing"]["cron"] == "0 7 * * *"
        assert jobs["morning-briefing"]["mission"] == "@pack:morning-briefing"
        assert jobs["memory-hygiene"]["cron"] == "0 9 * * 0"
        assert jobs["memory-hygiene"]["mission"] == "@pack:memory-hygiene"

        # idempotent
        second = packs.ensure_defaults(d)
        assert second == {"packs": [], "jobs": []}, second

        # user edits are sacred
        pd = packs.packs_dir(d)
        with open(os.path.join(pd, "morning-briefing.md"), "w") as f:
            f.write("USER EDIT")
        packs.ensure_defaults(d)
        with open(os.path.join(pd, "morning-briefing.md")) as f:
            assert f.read() == "USER EDIT"
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_run_due_expands_pack_refs_before_mission_fn():
    """Scheduler resolves @pack refs at the run_due seam, not in the model."""
    from lib import packs, sched
    d = tempfile.mkdtemp()
    try:
        pd = packs.packs_dir(d)
        os.makedirs(pd, exist_ok=True)
        with open(os.path.join(pd, "alpha.md"), "w") as f:
            f.write("PACK PAYLOAD")
        sched.add(d, "packy", "* * * * *", "Do X @pack:alpha now")
        got = []
        res = sched.run_due(d, lambda mission, name: got.append((mission, name)) or "ok")
        assert res and res["status"] == "ok", res
        assert got == [("Do X PACK PAYLOAD now", "sched-packy")], got
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_cli_pack_flags_wired():
    """--packs/--pack/--install-defaults exist and route to pack commands."""
    src = open(os.path.join(os.path.dirname(__file__), "..", "tony")).read()
    assert 'p.add_argument("--packs"' in src
    assert 'p.add_argument("--pack"' in src
    assert 'p.add_argument("--install-defaults"' in src
    assert "return cmd_install_defaults()" in src
    assert "return cmd_packs(args.pack)" in src

