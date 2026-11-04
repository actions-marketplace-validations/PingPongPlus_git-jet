import json
from datetime import date

import pytest
from PIL import Image

from git_jet.calendar import make_calendar
from git_jet.cli import main
from git_jet.export import Options, export
from git_jet.render import Renderer


@pytest.mark.parametrize("jets", (1, 3))
@pytest.mark.parametrize("carrier", ("lincoln", "classic"))
@pytest.mark.parametrize("water", ("ocean", "original"))
def test_real_cached_calendar_exports_exact_frames_without_network(
    tmp_path, monkeypatch, capsys, jets, carrier, water
):
    def forbidden(*args, **kwargs):
        raise AssertionError("cached or demo rendering must not use the network")

    monkeypatch.setattr("git_jet.github.GitHubClient.request", forbidden)
    monkeypatch.setenv("GITHUB_TOKEN", "never-save-this-test-token")
    calendar = make_calendar(
        "octocat", date(2026, 11, 1), 7, {date(2026, 10, 29): 8, date(2026, 11, 1): 2}
    )
    profile = tmp_path / "source.json"
    calendar.write(profile)
    output = tmp_path / "output"
    assert (
        main(
            [
                "render",
                "--calendar",
                str(profile),
                "--scale",
                "1",
                "--jets",
                str(jets),
                "--carrier",
                carrier,
                "--water",
                water,
                "--output-dir",
                str(output),
            ]
        )
        == 0
    )
    report = json.loads(capsys.readouterr().out)
    assert report["total_commits"] == 10
    assert report["attacks"] == report["active_days"] == 2
    assert report["decoded_frames_match"] and report["transparent"]
    assert report["source"] == "cache"
    assert report["jets"] == jets and len(report["flights"]) == jets
    assert report["carrier"] == carrier
    assert report["water"] == water
    assert report["graph_theme"] == "blue"
    assert sum(f["attacks"] for f in report["flights"]) == 2
    assert {t["jet"] for t in report["targets"]}.issubset(set(range(1, jets + 1)))
    renderer = Renderer(calendar, jets=jets, seed=report["seed"], carrier=carrier, water=water)
    with Image.open(output / "git-jet.png") as png:
        assert png.tobytes() == renderer.frame(0).tobytes()
        assert set(png.getchannel("A").tobytes()) == {0, 255}
    with Image.open(output / "git-jet.gif") as gif:
        assert gif.n_frames == report["frames"]
    assert all(b"never-save-this-test-token" not in p.read_bytes() for p in output.iterdir())


def test_oversized_export_preserves_previous_good_files(tmp_path, monkeypatch):
    saved = {
        name: b"previous asset"
        for name in ("git-jet.gif", "git-jet.png", "calendar.json", "report.json")
    }
    for name, data in saved.items():
        (tmp_path / name).write_bytes(data)
    monkeypatch.setattr("git_jet.export.MAX_BYTES", 10)
    renderer = Renderer(make_calendar("octocat", date(2026, 11, 1), 7, {}))
    with pytest.raises(ValueError, match="25 MB"):
        export(renderer, tmp_path, Options(scale=1))
    assert {name: (tmp_path / name).read_bytes() for name in saved} == saved
    assert sorted(path.name for path in tmp_path.iterdir()) == sorted(saved)


@pytest.mark.parametrize("options", ({"scale": 0}, {"scale": True}, {"fps": 12}, {"fps": "10"}))
def test_export_options_are_validated(options):
    with pytest.raises(ValueError):
        Options(**options)


def test_cached_period_cannot_silently_ignore_requested_dates(tmp_path, capsys):
    path = tmp_path / "calendar.json"
    make_calendar("octocat", date(2026, 11, 1), 7, {}).write(path)
    assert (
        main(
            [
                "render",
                "--calendar",
                str(path),
                "--days",
                "30",
                "--output-dir",
                str(tmp_path / "bad"),
            ]
        )
        == 1
    )
    assert "different day window" in capsys.readouterr().err
    assert not (tmp_path / "bad").exists()


def test_outside_window_dates_have_no_fabricated_empty_cells():
    renderer = Renderer(make_calendar("octocat", date(2026, 11, 1), 1, {}))
    # One selected day is one seven-pixel tile, rather than 370 invented empty days.
    grid = renderer.grid_frame(0)
    assert grid.getchannel("A").histogram()[255] == 20
