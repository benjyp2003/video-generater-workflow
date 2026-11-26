import shutil
import subprocess

from conftest import ROOT


def test_new_video_from_template(tmp_path):
    root = tmp_path / "studio"
    (root / "tools").mkdir(parents=True)
    shutil.copy(ROOT / "tools" / "new_video.sh", root / "tools")
    shutil.copytree(ROOT / "templates", root / "templates")
    r = subprocess.run(
        ["bash", "tools/new_video.sh", "docker-run", "concept", "What & why / docker"],
        cwd=root, capture_output=True, text=True, env={"NO_BRANCH": "1", "PATH": "/usr/bin:/bin"},
    )
    assert r.returncode == 0, r.stderr
    vids = list((root / "videos").iterdir())
    assert len(vids) == 1 and vids[0].name.endswith("-docker-run")
    manifest = (vids[0] / "video.yaml").read_text()
    assert "__" not in manifest
    assert "format: concept" in manifest
    assert 'title_working: "What & why / docker"' in manifest
    assert (vids[0] / "media" / "audio").is_dir()


def test_new_video_rejects_bad_format(tmp_path):
    r = subprocess.run(["bash", str(ROOT / "tools" / "new_video.sh"), "x", "vlog"],
                       capture_output=True, text=True)
    assert r.returncode == 2
