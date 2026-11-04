import json
from datetime import date, timedelta

import pytest
from PIL import Image

import git_jet.export as exporter
from git_jet.calendar import make_calendar
from git_jet.cli import main
from git_jet.demo import demo_calendar
from git_jet.export import Options, render_assets
from git_jet.limits import GifSizeLimitError


def test_live_render_automatically_fits_without_recollecting_or_skipping_targets(
    monkeypatch, tmp_path, capsys
):
    calendar = demo_calendar()
    expected_dates = {day.date.isoformat() for day in calendar.days if day.commits}
    collected = []

    def collect(*args, **kwargs):
        collected.append((args, kwargs))
        return calendar

    monkeypatch.setattr("git_jet.cli.GitHubClient.collect", collect)
    # Between the native and doubled-size demos, so this exercises scale-only
    # fallback even with the richer animated ocean surface.
    monkeypatch.setattr(exporter, "MAX_BYTES", 8_000_000)
    assert (
        main(
            [
                "render",
                "--username",
                "octocat",
                "--seed",
                "git-jet-loop",
                "--output-dir",
                str(tmp_path),
            ]
        )
        == 0
    )
    captured = capsys.readouterr()
    report = json.loads(captured.out)
    assert len(collected) == 1
    assert report["auto_compressed"] and report["requested_scale"] == 2 and report["scale"] == 1
    assert report["requested_fps"] == report["fps"] == 20
    assert report["seed"] == "git-jet-loop" and report["source"] == "live"
    assert report["carrier"] == "lincoln"
    assert report["attacks"] == report["active_days"] == len(expected_dates)
    assert sum(t["commits"] for t in report["targets"]) == calendar.total
    assert {t["date"] for t in report["targets"]} == expected_dates
    assert report["gif_bytes"] <= exporter.MAX_BYTES and report["decoded_frames_match"]
    assert json.loads((tmp_path / "report.json").read_text()) == report
    assert "retrying at 480x320, 20 FPS" in captured.err
    with Image.open(tmp_path / "git-jet.gif") as gif:
        assert gif.size == (480, 320) and gif.n_frames == report["frames"]
    with Image.open(tmp_path / "git-jet.png") as png:
        assert png.size == (480, 320)


def test_exhausted_fallbacks_leave_previous_assets_untouched(monkeypatch, tmp_path):
    saved = {name: b"previous asset" for name in exporter.ASSETS}
    for name, data in saved.items():
        (tmp_path / name).write_bytes(data)
    monkeypatch.setattr(exporter, "MAX_BYTES", 10)
    with pytest.raises(GifSizeLimitError, match="native scale and 5 FPS"):
        render_assets(demo_calendar(), tmp_path, Options(), seed="fixed")
    assert {name: (tmp_path / name).read_bytes() for name in saved} == saved
    assert sorted(p.name for p in tmp_path.iterdir()) == sorted(saved)


def test_auto_compression_can_be_disabled(monkeypatch, tmp_path):
    attempts = []

    def too_big(renderer, output, options, **kwargs):
        attempts.append(options)
        raise GifSizeLimitError("GIF exceeds 25 MB")

    monkeypatch.setattr(exporter, "export", too_big)
    with pytest.raises(GifSizeLimitError, match="25 MB"):
        render_assets(demo_calendar(), tmp_path, Options(), auto_compress=False)
    assert attempts == [Options()]


def test_scale_is_reduced_before_fps_with_one_fresh_seed_and_all_targets(monkeypatch, tmp_path):
    seeds = []
    attempts = []
    calendar = demo_calendar()
    expected_dates = {day.date for day in calendar.days if day.commits}

    def fresh_seed(size):
        seeds.append(size)
        return "keep-this-route"

    def fit(renderer, output, options, **kwargs):
        attempts.append(options)
        assert renderer.calendar is calendar
        assert renderer.flight.seed == "keep-this-route" and renderer.jet_count == 3
        assert renderer.carrier == "classic"
        assert renderer.water == "original"
        assert renderer.graph_theme == "github"
        assert len(renderer.flight.strikes) == len(expected_dates)
        assert {s.cell.day.date for s in renderer.flight.strikes} == expected_dates
        assert sum(s.cell.day.commits for s in renderer.flight.strikes) == calendar.total
        if options.fps == 20:
            raise GifSizeLimitError("GIF exceeds 25 MB")
        return {"fps": options.fps}

    monkeypatch.setattr("git_jet.flight.secrets.token_hex", fresh_seed)
    monkeypatch.setattr(exporter, "export", fit)
    assert render_assets(
        calendar,
        tmp_path,
        Options(),
        jets=3,
        carrier="classic",
        water="original",
        graph_theme="github",
    ) == {"fps": 10}
    assert attempts == [Options(2, 20), Options(1, 20), Options(1, 10)]
    assert len(seeds) == 1


def test_frame_limit_retries_at_a_supported_lower_fps(monkeypatch, tmp_path):
    end = date(2026, 11, 1)
    calendar = make_calendar("octocat", end, 365, {end - timedelta(days=i): 1 for i in range(365)})
    attempts = []

    def fit(renderer, output, options, **kwargs):
        attempts.append(options)
        assert renderer.frame_count <= 3000
        assert len(renderer.flight.strikes) == 365
        return {"fps": options.fps}

    monkeypatch.setattr(exporter, "export", fit)
    assert render_assets(calendar, tmp_path, Options(2, 25), seed="0") == {"fps": 20}
    assert attempts == [Options(1, 20)]


@pytest.mark.parametrize("error", (ValueError("invalid artwork"), OSError("write failed")))
def test_other_errors_are_not_hidden_by_retries(monkeypatch, tmp_path, error):
    attempts = []

    def broken(*args, **kwargs):
        attempts.append(1)
        raise error

    monkeypatch.setattr(exporter, "export", broken)
    with pytest.raises(type(error), match=str(error)):
        render_assets(demo_calendar(), tmp_path, Options())
    assert len(attempts) == 1
