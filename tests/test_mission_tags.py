"""P38 RED proof: lib.missiontags module does not exist yet."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def test_parse_mission_tag_valid_slug():
    import lib.missiontags
    result = lib.missiontags.parse_mission_tag("deploy-api")
    assert result == "deploy-api"


def test_parse_mission_tag_absent():
    import lib.missiontags
    result = lib.missiontags.parse_mission_tag("")
    assert result is None


def test_parse_mission_tag_malformed():
    import lib.missiontags
    result = lib.missiontags.parse_mission_tag("123-invalid!@#")
    assert result is None


def test_child_slug_namespacing_parent_tag():
    import lib.missiontags
    slug = lib.missiontags.child_slug("deploy-api", "build")
    assert slug == "deploy-api/build"


def test_child_timeout_halving_with_60s_floor():
    import lib.missiontags
    timeout = lib.missiontags.child_timeout(120)
    assert timeout == 60
    timeout2 = lib.missiontags.child_timeout(300)
    assert timeout2 == 150


def test_max_depth_constant():
    import lib.missiontags
    assert lib.missiontags.MAX_DEPTH == 2


def test_max_children_constant():
    import lib.missiontags
    assert lib.missiontags.MAX_CHILDREN == 2


def test_done_threshold_constant():
    import lib.missiontags
    assert lib.missiontags.DONE_THRESHOLD == 60


def test_depth_3_spawn_refusal():
    import lib.missiontags
    try:
        lib.missiontags.spawn_child(depth=3)
        assert False, "should have raised"
    except ValueError:
        assert True
