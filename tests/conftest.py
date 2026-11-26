import sys
from pathlib import Path
from textwrap import dedent

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

SCRIPT = dedent("""\
    ---
    schema_version: 1
    video: test-video
    ---
    ## s01 Hook
    [VISUAL] slide:title
    You type one command.

    ## s02 Client and daemon
    [VISUAL] diagram:cli-daemon highlight the socket
    [CLAIM] C1, C2
    [CMD] docker version
    The docker command is a client.
    It talks to a daemon.
    """)

RESEARCH = dedent("""\
    ## Claims ledger
    | id | claim | sources | status | notes |
    |----|-------|---------|--------|-------|
    | C1 | CLI talks to dockerd over an API | S1 | verified | |
    | C2 | dockerd uses containerd | S1, S2 | **verified** | |
    | C3 | Containers are VMs | — | rejected | misconception |
    """)

SOURCES = dedent("""\
    schema_version: 1
    sources:
      - {id: S1, title: Docker docs, url: "https://docs.docker.com/engine/"}
      - {id: S2, title: containerd, url: "https://containerd.io/docs/"}
    """)


@pytest.fixture
def video(tmp_path):
    d = tmp_path / "videos" / "test-video"
    (d / "demo").mkdir(parents=True)
    (d / "script.md").write_text(SCRIPT)
    (d / "research.md").write_text(RESEARCH)
    (d / "sources.yaml").write_text(SOURCES)
    (d / "demo" / "commands.sh").write_text("docker version\n")
    (d / "video.yaml").write_text("schema_version: 1\nid: test-video\nproviders: {tts: kokoro}\n")
    return d
