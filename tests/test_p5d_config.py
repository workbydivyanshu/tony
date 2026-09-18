"""P5d RED proof: config.load/set_role + tiers.assign_roles_with_sources."""
import sys, os, shutil, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib import tiers, catalog


# --- helpers ---

def _tmp_home():
    d = "/tmp/tony-test-p5d-home"
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d, exist_ok=True)
    return d


def _set_home(tmpdir):
    os.environ["HOME"] = tmpdir


def _restore_home():
    os.environ.pop("HOME", None)


# --- (a) config.load() on missing file -> {"roles": {}} defaults, no crash ---

def test_load_missing_file_defaults():
    from lib import config  # ImportError: config not defined
    tmpdir = _tmp_home()
    _set_home(tmpdir)
    r = config.load()
    assert r == {"roles": {}}
    _restore_home()
    shutil.rmtree(tmpdir, ignore_errors=True)


# --- (b) set_role/load round-trip preserves unknown keys (opencode_bin) ---

def test_set_role_load_preserves_unknown_keys():
    from lib import config  # ImportError: config not defined
    tmpdir = _tmp_home()
    _set_home(tmpdir)
    config.set_role("builder", "opencode/big-pickle")
    r = config.load()
    assert r["roles"]["builder"] == "opencode/big-pickle"
    assert "opencode_bin" in r
    _restore_home()
    shutil.rmtree(tmpdir, ignore_errors=True)


# --- (c) corrupt JSON -> defaults + warning, no raise ---

def test_load_corrupt_json_defaults():
    from lib import config  # ImportError: config not defined
    tmpdir = _tmp_home()
    _set_home(tmpdir)
    cfg_path = os.path.join(tmpdir, ".tony", "config.json")
    os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
    with open(cfg_path, "w") as f:
        f.write("{bad json!!!")
    r = config.load()
    assert r == {"roles": {}}
    _restore_home()
    shutil.rmtree(tmpdir, ignore_errors=True)


# --- (d) unknown role on set -> KeyError; bad regex on set -> re.error ---

def test_set_role_unknown_raises_keyerror():
    from lib import config  # ImportError: config not defined
    tmpdir = _tmp_home()
    _set_home(tmpdir)
    try:
        config.set_role("nope", "opencode/big-pickle")
    except KeyError:
        pass
    else:
        assert False, "expected KeyError"
    finally:
        _restore_home()
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_set_role_bad_regex_raises_re_error():
    from lib import config  # ImportError: config not defined
    tmpdir = _tmp_home()
    _set_home(tmpdir)
    try:
        config.set_role("builder", "[invalid")
    except re.error:
        pass
    else:
        assert False, "expected re.error"
    finally:
        _restore_home()
        shutil.rmtree(tmpdir, ignore_errors=True)


# --- (e) tiers.assign_roles_with_sources(catalog, {matching override}) -> builder pinned with source "override" ---

def test_assign_roles_with_sources_override_matches():
    catalog = ["opencode/big-pickle", "opencode/muse-spark-1.3-contributor-free"]
    overrides = {"builder": r"big-pickle"}
    r = tiers.assign_roles_with_sources(catalog, overrides)  # AttributeError
    assert r["builder"]["model"] == "opencode/big-pickle"
    assert r["builder"]["source"] == "override"


# --- (f) override matching nothing -> tier-default model + source "tier-default" ---

def test_assign_roles_with_sources_no_match_falls_back():
    catalog = ["opencode/big-pickle", "opencode/muse-spark-1.3-contributor-free"]
    overrides = {"builder": r"nomatch-here"}
    r = tiers.assign_roles_with_sources(catalog, overrides)  # AttributeError
    assert r["builder"]["source"] == "tier-default"
    assert r["builder"]["model"] in catalog


# --- (g) overrides=None -> identical to legacy assign_roles ---

def test_assign_roles_with_sources_none_equals_legacy():
    catalog = ["opencode/nemotron-3-ultra", "opencode/ling-3.0-flash", "opencode/big-pickle"]
    legacy = tiers.assign_roles(catalog)
    r = tiers.assign_roles_with_sources(catalog, None)  # AttributeError
    assert r == legacy


def test_clear_role_noop_writes_nothing():
    from lib import config
    tmpdir = _tmp_home()
    _set_home(tmpdir)
    config.clear_role("builder")
    assert not os.path.exists(os.path.join(tmpdir, ".tony", "config.json"))
    _restore_home()
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_get_roles_wrong_shape_defaults():
    from lib import config
    tmpdir = _tmp_home()
    _set_home(tmpdir)
    cfg_path = os.path.join(tmpdir, ".tony", "config.json")
    os.makedirs(os.path.dirname(cfg_path), exist_ok=True)
    open(cfg_path, "w").write('{"roles": null}')
    assert config.get_roles() == {}
    config.clear_role("builder")
    assert config.get_roles() == {}
    _restore_home()
    shutil.rmtree(tmpdir, ignore_errors=True)


def test_validate_warns_on_no_match():
    from lib import config
    catalog = ["opencode/big-pickle"]
    assert config.validate(catalog) == []
