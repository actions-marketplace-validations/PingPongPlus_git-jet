import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from git_jet.demo import demo_calendar

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("action_script", ROOT / "scripts/run_action.py")
action = importlib.util.module_from_spec(spec)
spec.loader.exec_module(action)


def test_action_forwards_inputs_and_writes_only_successful_output(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "outputs"))
    monkeypatch.setenv("JET_USERNAME", "octocat")
    monkeypatch.setenv("JET_DAYS", "30")
    monkeypatch.setenv("JET_JETS", "3")
    monkeypatch.setenv("JET_CARRIER", "classic")
    monkeypatch.setenv("JET_WATER", "original")
    monkeypatch.setenv("JET_GRAPH_THEME", "github")
    monkeypatch.setenv("JET_AUTO_COMPRESS", "false")
    monkeypatch.setenv("JET_OUTPUT_DIR", "generated")
    monkeypatch.setenv("JET_SEED", "reproducible-action-route")
    args = []

    def collect(argv):
        args.extend(argv)
        return 0

    monkeypatch.setattr(action, "main", collect)
    assert action.run() == 0
    assert args[0] == "render"
    assert args[args.index("--username") + 1] == "octocat"
    assert args[args.index("--days") + 1] == "30"
    assert args[args.index("--jets") + 1] == "3"
    assert args[args.index("--carrier") + 1] == "classic"
    assert args[args.index("--water") + 1] == "original"
    assert args[args.index("--graph-theme") + 1] == "github"
    assert "--no-auto-compress" in args
    assert args[args.index("--seed") + 1] == "reproducible-action-route"
    outputs = dict(line.split("=", 1) for line in (tmp_path / "outputs").read_text().splitlines())
    assert outputs["calendar"] == str(tmp_path / "generated/calendar.json")
    assert outputs["gif"] == str(tmp_path / "generated/git-jet.gif")
    assert outputs["png"] == str(tmp_path / "generated/git-jet.png")
    assert Path(outputs["publish-script"]).is_file()


def test_action_rejects_output_escape_before_collecting(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("JET_OUTPUT_DIR", "../outside")
    monkeypatch.setattr(action, "main", lambda argv: (_ for _ in ()).throw(AssertionError()))
    assert action.run() == 1


def test_action_rejects_invalid_auto_compress_before_collecting(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("JET_REPOSITORY_OWNER", "octocat")
    monkeypatch.setenv("JET_AUTO_COMPRESS", "maybe")
    monkeypatch.setattr(action, "main", lambda argv: (_ for _ in ()).throw(AssertionError()))
    assert action.run() == 1


def test_action_does_not_publish_an_output_when_collection_fails(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_WORKSPACE", str(tmp_path))
    monkeypatch.setenv("GITHUB_OUTPUT", str(tmp_path / "outputs"))
    monkeypatch.setenv("JET_USERNAME", "octocat")
    monkeypatch.delenv("JET_OUTPUT_DIR", raising=False)
    monkeypatch.setattr(action, "main", lambda argv: 1)
    assert action.run() == 1
    assert not (tmp_path / "outputs").exists()


@pytest.mark.parametrize("carrier", ("lincoln", "classic"))
@pytest.mark.parametrize("water", ("ocean", "original"))
def test_actual_action_script_generates_demo_assets_and_returns_paths(tmp_path, carrier, water):
    calendar = demo_calendar()
    expected_dates = {day.date.isoformat() for day in calendar.days if day.commits}
    process = subprocess.run(
        [sys.executable, str(ROOT / "scripts/run_action.py")],
        env={
            **os.environ,
            "PYTHONPATH": str(ROOT / "src"),
            "GITHUB_WORKSPACE": str(tmp_path),
            "GITHUB_OUTPUT": str(tmp_path / "outputs"),
            "JET_REPOSITORY_OWNER": "octocat",
            "JET_USERNAME": "",
            "JET_DEMO": "true",
            "JET_SCALE": "1",
            "JET_OUTPUT_DIR": "rendered",
            "JET_SEED": "action-smoke",
            "JET_JETS": "3",
            "JET_CARRIER": carrier,
            "JET_WATER": water,
            "JET_GRAPH_THEME": "github",
            "JET_AUTO_COMPRESS": "true",
            "GITHUB_TOKEN": "never-save-this-test-token",
        },
        text=True,
        capture_output=True,
    )
    assert process.returncode == 0, process.stderr
    report = json.loads(process.stdout)
    assert report["source"] == "demo" and report["attacks"] == len(expected_dates)
    assert report["total_commits"] == calendar.total
    assert {target["date"] for target in report["targets"]} == expected_dates
    assert report["seed"] == "action-smoke"
    assert report["jets"] == 3 and len(report["flights"]) == 3
    assert report["carrier"] == carrier
    assert report["water"] == water
    assert report["graph_theme"] == "github"
    assert sum(f["attacks"] for f in report["flights"]) == report["attacks"]
    assert report["decoded_frames_match"]
    outputs = dict(line.split("=", 1) for line in (tmp_path / "outputs").read_text().splitlines())
    assert all(
        Path(outputs[name]).is_file() for name in ("gif", "png", "calendar", "publish-script")
    )
