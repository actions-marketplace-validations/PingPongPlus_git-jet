"""Rebuild both README demos from the same fixed synthetic calendar."""

from pathlib import Path

from git_jet.calendar import Calendar
from git_jet.export import Options, render_assets


def main():
    root = Path(__file__).resolve().parents[1]
    calendar = Calendar.read(root / "examples/demo/calendar.json")
    for carrier, folder, graph_theme in (
        ("lincoln", "demo", "blue"),
        ("classic", "demo-classic", "github"),
    ):
        report = render_assets(
            calendar,
            root / "examples" / folder,
            Options(),
            jets=3,
            carrier=carrier,
            graph_theme=graph_theme,
            seed="git-jet-loop",
            source="demo",
        )
        print(
            f"{carrier}: {report['attacks']} attacks, {report['duration_seconds']} seconds, "
            f"{report['width']}x{report['height']}, {report['gif_bytes']} bytes"
        )


if __name__ == "__main__":
    main()
