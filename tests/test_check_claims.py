from tools.check_claims import check, main


def test_clean_video_passes(video):
    errors, warnings = check(video)
    assert errors == []
    assert any("s01" in w and "without [CLAIM]" in w for w in warnings)


def test_unverified_claim_is_error(video):
    r = video / "research.md"
    r.write_text(r.read_text().replace("| S1 | verified |", "| S1 | assumption |"))
    errors, _ = check(video)
    assert any("C1 with status 'assumption'" in e for e in errors)
    assert main(["x", str(video)]) == 1


def test_missing_claim_and_source(video):
    s = video / "script.md"
    s.write_text(s.read_text().replace("[CLAIM] C1, C2", "[CLAIM] C1, C9"))
    (video / "sources.yaml").write_text("sources: [{id: S1}]\n")
    errors, _ = check(video)
    assert any("C9, which is not in research.md" in e for e in errors)


def test_missing_source_id(video):
    (video / "sources.yaml").write_text("sources: [{id: S1}]\n")
    errors, _ = check(video)
    assert any("cites S2, missing from sources.yaml" in e for e in errors)


def test_command_not_in_demo_warns(video):
    (video / "demo" / "commands.sh").write_text("echo hi\n")
    errors, warnings = check(video)
    assert errors == []
    assert any("docker version" in w for w in warnings)
