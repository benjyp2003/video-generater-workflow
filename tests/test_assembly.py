import shutil
import subprocess

import pytest

from tools import storyboard
from tools.assemble import assemble, duration, missing_inputs
from tools.tts import run as tts_run

pytestmark = pytest.mark.skipif(not shutil.which("ffmpeg"), reason="ffmpeg not installed")


def make_png(path, color="red"):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    f"color=c={color}:s=640x360", "-frames:v", "1", str(path)], check=True)


def make_clip(path, seconds=1):
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i",
                    "testsrc=s=640x360:r=30", "-t", str(seconds), str(path)], check=True)


def test_storyboard_resolves_and_overrides(video):
    make_png(video / "media" / "visuals" / "title.png")
    (video / "storyboard.overrides.yaml").write_text("s01: {motion: zoom, pad_after_s: 1}\n")
    sb = storyboard.build(video)
    s01, s02 = sb["scenes"]
    assert s01["visuals"][0]["src"] == "media/visuals/title.png"
    assert s01["motion"] == "zoom" and s01["pad_after_s"] == 1.0
    assert s02["visuals"][0]["src"] is None
    assert sb["resolution"] == "1920x1080"


def test_missing_inputs_block_final_render(video):
    with pytest.raises(SystemExit, match="missing inputs"):
        assemble(video)
    sb = storyboard.build(video)
    assert any("cli-daemon" in m for m in missing_inputs(video, sb))


def test_draft_and_final_render(video, capsys):
    tts_run(video, None, False, "placeholder")
    draft = assemble(video, draft=True)
    assert draft.name == "draft.mp4" and duration(draft) > 2

    make_png(video / "media" / "visuals" / "title.png")
    make_png(video / "media" / "visuals" / "cli-daemon.png", "blue")
    make_clip(video / "media" / "raw" / "run-hello.mp4", seconds=6)
    (video / "storyboard.overrides.yaml").write_text(
        "s02:\n  visuals: [{type: diagram, name: cli-daemon}, {type: terminal, name: run-hello}]\n")
    final = assemble(video)
    # s01 = 2s minimum; s02 stretched to the 6s clip (longer than 4.4s narration)
    assert 7.5 < duration(final) < 9

    capsys.readouterr()
    assemble(video)
    assert capsys.readouterr().out.count("up to date") == 2
