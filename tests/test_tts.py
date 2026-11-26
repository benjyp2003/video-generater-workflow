import json
import wave

from tools.tts import apply_pronunciations, run


def test_pronunciations_whole_words_only():
    m = {"runc": "run-see", "containerd": "container-dee"}
    assert apply_pronunciations("runc and containerd", m) == "run-see and container-dee"
    assert apply_pronunciations("runcible containerd-shim", m) == "runcible containerd-shim"
    assert apply_pronunciations("type `docker run`", {}) == "type docker run"


def test_placeholder_generates_and_caches(video, capsys):
    assert run(video, None, False, "placeholder") == 0
    wav = video / "media" / "audio" / "s02.wav"
    with wave.open(str(wav)) as w:
        assert w.getframerate() == 24000 and w.getnframes() > 0
    fps = json.loads((video / "media" / "audio" / ".fingerprints.json").read_text())
    assert set(fps) == {"s01", "s02"}

    capsys.readouterr()
    run(video, None, False, "placeholder")
    assert capsys.readouterr().out.count("up to date") == 2

    s = video / "script.md"
    s.write_text(s.read_text().replace("It talks to a daemon.", "It talks to the daemon."))
    run(video, None, False, "placeholder")
    out = capsys.readouterr().out
    assert "generated: " in out and "s02.wav" in out and "up to date: s01" in out


def test_scene_filter_and_unknown_scene(video):
    assert run(video, ["s01"], False, "placeholder") == 0
    assert (video / "media" / "audio" / "s01.wav").exists()
    assert not (video / "media" / "audio" / "s02.wav").exists()
    assert run(video, ["s99"], False, "placeholder") == 2


def test_human_provider_reports_missing(video, capsys):
    assert run(video, None, False, "human") == 1
    assert "record:" in capsys.readouterr().out
