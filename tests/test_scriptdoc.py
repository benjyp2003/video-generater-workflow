import pytest

from tools.scriptdoc import ParseError, load_claims, load_script, parse_script, parse_visual


def test_parses_scenes_markers_and_narration(video):
    script = load_script(video)
    assert script.meta["video"] == "test-video"
    assert [s.id for s in script.scenes] == ["s01", "s02"]
    s02 = script.scene("s02")
    assert s02.title == "Client and daemon"
    assert s02.claims == ["C1", "C2"]
    assert s02.commands == ["docker version"]
    assert s02.visuals[0].type == "diagram"
    assert s02.visuals[0].name == "cli-daemon"
    assert s02.visuals[0].note == "highlight the socket"
    assert s02.narration == "The docker command is a client. It talks to a daemon."


def test_inserted_scene_ids_allowed():
    s = parse_script("## s02a Extra\nHello.\n")
    assert s.scenes[0].id == "s02a"


def test_duplicate_scene_rejected():
    with pytest.raises(ParseError, match="duplicate scene id s01"):
        parse_script("## s01 A\nx\n## s01 B\ny\n")


def test_bad_visual_rejected():
    with pytest.raises(ParseError):
        parse_visual("diagram")


def test_unclosed_front_matter():
    with pytest.raises(ParseError):
        parse_script("---\na: 1\n## s01 x\n")


def test_claims_ledger(video):
    claims = load_claims(video)
    assert set(claims) == {"C1", "C2", "C3"}
    assert claims["C2"].status == "verified"   # bold markup stripped
    assert claims["C2"].sources == ["S1", "S2"]
    assert claims["C3"].sources == []
