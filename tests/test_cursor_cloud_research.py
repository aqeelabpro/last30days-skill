"""Cursor Cloud research profile: cookie lock, Polymarket exclusion, refusals."""

import json
import os
import re
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / ".cursor" / "research.sh"
DOCKERFILE = ROOT / ".cursor" / "Dockerfile"
ENVIRONMENT = ROOT / ".cursor" / "environment.json"

REFUSED = ("setup", "doctor", "Doctor", "--publish-html", "--allow-browser-cookies", "--probe")


def _run(args, *, python=None, extra_env=None):
    env = os.environ.copy()
    env.pop("EXCLUDE_SOURCES", None)
    if python is not None:
        env["LAST30DAYS_PYTHON"] = str(python)
    if extra_env:
        env.update(extra_env)
    return subprocess.run(
        ["bash", str(WRAPPER), *args],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )


def test_wrapper_is_executable_and_dockerfile_pins_a_checksum():
    mode = WRAPPER.stat().st_mode
    assert mode & stat.S_IXUSR
    text = DOCKERFILE.read_text(encoding="utf-8")
    assert "sha256sum -c -" in text
    assert not re.search(r"\|\s*(?:ba)?sh\b", text)
    assert "USER ubuntu" in text
    assert "EXCLUDE_SOURCES=polymarket" in text
    assert "FROM_BROWSER=off" in text
    config = json.loads(ENVIRONMENT.read_text(encoding="utf-8"))
    assert config["user"] == "ubuntu"
    assert config["build"]["dockerfile"] == "Dockerfile"
    assert "install" in config
    assert "start" not in config


def test_wrapper_refuses_setup_doctor_publish_and_cookie_opt_in():
    for arg in REFUSED:
        proc = _run([arg])
        assert proc.returncode == 2, proc.stderr
        assert "refused" in proc.stderr


def test_wrapper_research_forces_locks_and_excludes_polymarket(tmp_path):
    recorder = tmp_path / "python-recorder"
    out = tmp_path / "args.txt"
    recorder.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            import os
            import sys
            from pathlib import Path
            Path({str(out)!r}).write_text(
                "\\n".join(sys.argv[1:])
                + "\\nEXCLUDE=" + os.environ.get("EXCLUDE_SOURCES", "")
                + "\\nFROM=" + os.environ.get("FROM_BROWSER", "")
                + "\\nCONSENT=" + os.environ.get("BROWSER_CONSENT", "")
                + "\\nAGENTCOOKIE=" + os.environ.get("AGENTCOOKIE", "")
                + "\\nNATIVE=" + os.environ.get("LAST30DAYS_NATIVE_SEARCH", "")
                + "\\n",
                encoding="utf-8",
            )
            """
        ),
        encoding="utf-8",
    )
    recorder.chmod(0o755)
    proc = _run(
        ["battery recycling ideas", "--emit=compact"],
        python=recorder,
        extra_env={"LAST30DAYS_MEMORY_DIR": str(tmp_path / "out")},
    )
    assert proc.returncode == 0, proc.stderr
    recorded = out.read_text(encoding="utf-8")
    assert "--no-browser-cookies" in recorded.splitlines()[0] or "--no-browser-cookies" in recorded
    assert "battery recycling ideas" in recorded
    assert "EXCLUDE=polymarket" in recorded
    assert "FROM=off" in recorded
    assert "CONSENT=false" in recorded
    assert "AGENTCOOKIE=off" in recorded
    assert "NATIVE=1" in recorded


def test_wrapper_appends_polymarket_to_an_existing_exclusion(tmp_path):
    recorder = tmp_path / "python-recorder"
    out = tmp_path / "args.txt"
    recorder.write_text(
        textwrap.dedent(
            f"""\
            #!/usr/bin/env python3
            import os
            from pathlib import Path
            Path({str(out)!r}).write_text(os.environ.get("EXCLUDE_SOURCES", ""), encoding="utf-8")
            """
        ),
        encoding="utf-8",
    )
    recorder.chmod(0o755)
    proc = _run(
        ["ideas"],
        python=recorder,
        extra_env={
            "EXCLUDE_SOURCES": "github",
            "LAST30DAYS_MEMORY_DIR": str(tmp_path / "out"),
        },
    )
    assert proc.returncode == 0, proc.stderr
    assert out.read_text(encoding="utf-8") == "github,polymarket"


def test_mock_research_does_not_call_polymarket(tmp_path):
    save = tmp_path / "reports"
    proc = _run(
        ["battery recycling ideas", "--mock", "--emit=compact", "--save-dir", str(save)],
        python=sys.executable,
        extra_env={"LAST30DAYS_MEMORY_DIR": str(save)},
    )
    assert proc.returncode == 0, proc.stderr
    combined = proc.stdout + proc.stderr
    assert "polymarket.com" not in combined.lower()
    assert "gamma-api.polymarket.com" not in combined.lower()
    saved = list(save.rglob("*.md"))
    assert saved, "mock research did not write a report"
    report = saved[0].read_text(encoding="utf-8")
    assert "battery recycling ideas" in report
    assert "polymarket.com" not in report.lower()
