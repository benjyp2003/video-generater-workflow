from tools.preflight import preflight

PUBLISH = """\
title: What happens when you run docker run?
description: |
  Summary.
  Sources:
  - https://docs.docker.com/engine/
visibility: private
made_for_kids: false
altered_or_synthetic: false
thumbnail: thumbnail.png
captions: final.srt
"""


def ready(video):
    (video / "publish.yaml").write_text(PUBLISH)
    (video / "thumbnail.png").write_bytes(b"png")
    (video / "final.srt").write_text("1\n")
    (video / "media" / "build").mkdir(parents=True)
    (video / "media" / "build" / "final.mp4").write_bytes(b"mp4")
    (video / "video.yaml").write_text(
        "approvals: {technical: {by: me}, final_qa: {by: me}, publish: null}\n")


def test_fresh_video_fails_everything(video):
    problems = preflight(video)
    assert any("approvals.technical" in p for p in problems)
    assert any("title is empty" in p for p in problems)
    assert any("missing media/build/final.mp4" in p for p in problems)


def test_ready_video_passes(video):
    ready(video)
    assert preflight(video) == []


def test_public_visibility_blocked(video):
    ready(video)
    (video / "publish.yaml").write_text(PUBLISH.replace("private", "public"))
    assert any("visibility" in p for p in preflight(video))


def test_secret_detected(video):
    ready(video)
    (video / "demo" / "commands.sh").write_text("docker version\nexport KEY=AKIAABCDEFGHIJKLMNOP\n")
    assert any("possible secret" in p for p in preflight(video))


def test_undecided_disclosure_blocked(video):
    ready(video)
    (video / "publish.yaml").write_text(PUBLISH.replace("altered_or_synthetic: false",
                                                        "altered_or_synthetic: null"))
    assert any("altered_or_synthetic" in p for p in preflight(video))
