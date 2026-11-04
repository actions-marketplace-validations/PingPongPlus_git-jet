import pytest
from PIL import ImageColor

from git_jet.art import GITHUB_GRID, commit_tile
from git_jet.cli import main
from git_jet.demo import demo_calendar
from git_jet.flight import GRID_Y
from git_jet.render import Renderer


def test_blue_remains_the_default_for_tiles_and_scenes():
    for level in range(5):
        for destroyed in (False, True):
            assert (
                commit_tile(level, destroyed).tobytes()
                == commit_tile(level, destroyed, theme="blue").tobytes()
            )
    default = Renderer(demo_calendar(), seed="graph-colors")
    blue = Renderer(demo_calendar(), seed="graph-colors", graph_theme="blue")
    assert default.graph_theme == "blue"
    assert default.frame(0).tobytes() == blue.frame(0).tobytes()


@pytest.mark.parametrize("level", (1, 2, 3, 4))
def test_github_theme_uses_flat_green_activity_levels(level):
    tile = commit_tile(level, theme="github")
    green = ImageColor.getcolor(GITHUB_GRID[level], "RGBA")
    assert tile.getpixel((3, 3)) == green
    assert {color for _, color in tile.getcolors() if color[3]} == {green}


def test_github_destroyed_days_become_transparent_empty_cells():
    empty = commit_tile(0, theme="github")
    assert empty.getpixel((3, 3))[3] == 0
    for level in range(1, 5):
        assert commit_tile(level, True, theme="github").tobytes() == empty.tobytes()


def test_graph_theme_preserves_flight_targets_clearing_and_scene_geometry():
    blue = Renderer(demo_calendar(), seed="graph-colors", graph_theme="blue")
    green = Renderer(demo_calendar(), seed="graph-colors", graph_theme="github")
    assert blue.flight.strikes == green.flight.strikes
    assert blue.frame_count == green.frame_count
    frames = {0, blue.frame_count - 1, *(s.hit for s in blue.flight.strikes)}
    for frame in frames:
        assert (
            blue.grid_frame(frame).getchannel("A").tobytes()
            == green.grid_frame(frame).getchannel("A").tobytes()
        )
    assert (
        blue.frame(0).crop((0, 0, 480, GRID_Y)).tobytes()
        == green.frame(0).crop((0, 0, 480, GRID_Y)).tobytes()
    )
    assert blue.grid_frame(0).tobytes() != green.grid_frame(0).tobytes()
    assert green.grid_frame(green.frame_count - 1).tobytes() == green.grid_frame(0).tobytes()


@pytest.mark.parametrize("theme", ("unknown", None, [], True))
def test_invalid_graph_themes_are_rejected(theme):
    with pytest.raises(ValueError, match="graph theme"):
        Renderer(demo_calendar(), graph_theme=theme)


def test_cli_rejects_unknown_graph_theme_before_collecting(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("invalid graph theme must not collect data")

    monkeypatch.setattr("git_jet.cli.GitHubClient.collect", forbidden)
    with pytest.raises(SystemExit) as error:
        main(["render", "--username", "octocat", "--graph-theme", "unknown"])
    assert error.value.code == 2
