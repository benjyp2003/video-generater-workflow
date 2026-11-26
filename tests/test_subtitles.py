import shutil

import pytest

from tools.subtitles import apply_glossary, chunk_text, script_cues, to_srt, ts


def test_timestamp_format():
    assert ts(0) == "00:00:00,000"
    assert ts(3723.4567) == "01:02:03,457"


def test_chunking_respects_line_length():
    text = "The docker command you type is just a client. " * 3
    cues = chunk_text(text)
    assert len(cues) == 3
    for c in cues:
        assert all(len(line) <= 42 for line in c.splitlines())
        assert len(c.splitlines()) <= 2
    assert chunk_text("type `docker run` now") == ["type docker run now"]


def test_glossary_fix_is_case_insensitive_and_whole_word():
    g = {"container d": "containerd", "run c": "runc"}
    assert apply_glossary("Then Container D calls run c.", g) == "Then containerd calls runc."
    assert apply_glossary("run cycle", g) == "run cycle"


def test_srt_render():
    srt = to_srt([(0, 1.5, "Hello"), (1.5, 3, "World")])
    assert srt.startswith("1\n00:00:00,000 --> 00:00:01,500\nHello\n")
    assert "2\n00:00:01,500 --> 00:00:03,000\nWorld" in srt


@pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")
def test_script_cues_follow_scene_offsets(video):
    from tools.assemble import assemble, duration
    from tools.tts import run as tts_run
    tts_run(video, None, False, "placeholder")
    assemble(video, draft=True)
    cues = script_cues(video)
    s01_len = duration(video / "media" / "build" / "segments" / "s01.mp4")
    assert cues[0][0] == 0 and cues[0][2] == "You type one command."
    s02 = [c for c in cues if "client" in c[2]][0]
    assert s02[0] == pytest.approx(s01_len)
    assert all(a < b for a, b, _ in cues)
