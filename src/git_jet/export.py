"""Stream a shared-palette GIF; audit decoded frames before replacing good assets."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from array import array
from dataclasses import dataclass
from pathlib import Path

from PIL import GifImagePlugin, Image, ImageChops, ImageColor

from . import art
from .calendar import Calendar
from .flight import HEIGHT, WIDTH, route_seed
from .limits import FrameLimitError, GifSizeLimitError
from .render import Renderer
from .water import COLORS as WATER_COLORS
from .water import DEFAULT_WATER

ASSETS = ("git-jet.gif", "git-jet.png", "report.json", "calendar.json")
MAX_BYTES = 25_000_000


@dataclass(frozen=True)
class Options:
    scale: int = 2
    fps: int = 20

    def __post_init__(self):
        if type(self.scale) is not int or not 1 <= self.scale <= 4:
            raise ValueError("scale must be an integer in 1..4")
        if type(self.fps) is not int or self.fps not in (5, 10, 20, 25):
            raise ValueError("fps must be 5, 10, 20 or 25")


def palette():
    samples = [
        *(art.carrier_sprite(carrier=carrier) for carrier in art.CARRIERS),
        *(art.commit_tile(i, theme=theme) for theme in art.GRAPH_THEMES for i in range(5)),
        *(art.explosion_sprite(i / 10) for i in range(10)),
        *(art.jet_sprite(0, thrust, bank) for thrust in range(3) for bank in (-1, 0, 1)),
    ]
    colors = sorted(
        {
            *(color for sample in samples for _, color in sample.getcolors(256) if color[3]),
            *(ImageColor.getcolor(color, "RGBA") for color in WATER_COLORS),
        }
    )
    if len(colors) > 255 or any(color[3] != 255 for color in colors):
        raise ValueError("artwork must fit 255 opaque colors plus transparency")
    entries = [(0, 0, 0, 0), *colors]
    mapping = {
        int.from_bytes(bytes(color), sys.byteorder): index for index, color in enumerate(entries)
    }
    rgb = [v for color in entries for v in color[:3]]
    return mapping, rgb + [0] * (768 - len(rgb))


def indexed(frame, mapping, rgb, scale):
    pixels = array("I", frame.tobytes())
    image = Image.frombytes("P", frame.size, bytes(mapping[p] for p in pixels))
    image.putpalette(rgb)
    image.info["transparency"] = 0
    if scale != 1:
        image = image.resize((WIDTH * scale, HEIGHT * scale), Image.Resampling.NEAREST)
    return image


def verify(path: Path, renderer: Renderer, options: Options):
    with Image.open(path) as gif:
        if gif.n_frames != renderer.frame_count or gif.info.get("loop") != 0:
            raise ValueError("GIF frame count or looping metadata changed")
        for index in range(gif.n_frames):
            gif.seek(index)
            expected = renderer.frame(index).resize(gif.size, Image.Resampling.NEAREST)
            actual = gif.convert("RGBA")
            alpha = expected.getchannel("A")
            if ImageChops.difference(alpha, actual.getchannel("A")).getbbox():
                raise ValueError(f"GIF transparency changed at frame {index}")
            difference = ImageChops.difference(expected.convert("RGB"), actual.convert("RGB"))
            if ImageChops.multiply(difference, alpha.convert("RGB")).getbbox():
                raise ValueError(f"GIF colors changed at frame {index}")
            if gif.info["duration"] != 1000 // options.fps or gif.disposal_method != 2:
                raise ValueError("GIF timing or transparent cleanup changed")


def export(
    renderer: Renderer,
    output: Path,
    options: Options,
    *,
    source="live",
    requested_options: Options | None = None,
):
    if renderer.flight.fps != options.fps:
        raise ValueError("renderer FPS differs from export FPS; rebuild the renderer")
    if renderer.frame_count * WIDTH * HEIGHT > 460_800_000:
        raise FrameLimitError("animation exceeds the render budget; select fewer days")
    requested_options = requested_options or options
    output.mkdir(parents=True, exist_ok=True)
    mapping, rgb = palette()
    with tempfile.TemporaryDirectory(prefix=".git-jet-", dir=output) as scratch:
        root = Path(scratch)
        gif = root / "git-jet.gif"
        with gif.open("wb") as stream:
            for index in range(renderer.frame_count):
                frame = indexed(renderer.frame(index), mapping, rgb, options.scale)
                if index == 0:
                    header, _ = GifImagePlugin.getheader(frame, info={"loop": 0, "transparency": 0})
                    for block in header:
                        stream.write(block)
                for block in GifImagePlugin.getdata(
                    frame, duration=1000 // options.fps, disposal=2, transparency=0
                ):
                    stream.write(block)
                if stream.tell() + 1 > MAX_BYTES:
                    raise GifSizeLimitError("GIF exceeds 25 MB; reduce scale or the selected days")
            stream.write(b";")
        first = renderer.frame(0).resize(
            (WIDTH * options.scale, HEIGHT * options.scale), Image.Resampling.NEAREST
        )
        first.save(root / "git-jet.png")
        verify(gif, renderer, options)
        renderer.calendar.write(root / "calendar.json")
        report = {
            "username": renderer.calendar.username,
            "source": source,
            "scope": renderer.calendar.to_dict()["scope"],
            "start_date": renderer.calendar.days[0].date.isoformat(),
            "end_date": renderer.calendar.days[-1].date.isoformat(),
            "days": len(renderer.calendar.days),
            "total_commits": renderer.calendar.total,
            "active_days": len(renderer.flight.strikes),
            "attacks": len(renderer.flight.strikes),
            "attack_mode": "day-cell",
            "jets": renderer.jet_count,
            "carrier": renderer.carrier,
            "water": renderer.water,
            "graph_theme": renderer.graph_theme,
            "seed": renderer.flight.seed,
            "flights": [
                {
                    "jet": flight.jet_id + 1,
                    "seed": flight.seed,
                    "attacks": len(flight.strikes),
                    "launch_frame": flight.launch_start,
                    "landed_frame": flight.landed,
                }
                for flight in renderer.flights
            ],
            "maneuvers": renderer.flight.maneuvers,
            "width": WIDTH * options.scale,
            "height": HEIGHT * options.scale,
            "scale": options.scale,
            "requested_scale": requested_options.scale,
            "requested_fps": requested_options.fps,
            "auto_compressed": options != requested_options,
            "frames": renderer.frame_count,
            "fps": options.fps,
            "duration_seconds": renderer.frame_count / options.fps,
            "transparent": True,
            "decoded_frames_match": True,
            "gif_bytes": gif.stat().st_size,
            "targets": [
                {
                    "date": s.cell.day.date.isoformat(),
                    "jet": s.jet_id + 1,
                    "commits": s.cell.day.commits,
                    "column": s.cell.column,
                    "row": s.cell.row,
                    "fire_frame": s.fire,
                    "hit_frame": s.hit,
                }
                for s in renderer.flight.strikes
            ],
        }
        (root / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        for name in ASSETS:
            os.replace(root / name, output / name)
    return report


def render_assets(
    calendar: Calendar,
    output: Path,
    options: Options,
    *,
    jets=1,
    carrier=art.DEFAULT_CARRIER,
    water=DEFAULT_WATER,
    graph_theme=art.DEFAULT_GRAPH_THEME,
    seed=None,
    source="live",
    auto_compress=True,
):
    """Fit the same complete calendar and seed, lowering scale before FPS."""
    seed = route_seed(seed)
    rates = [options.fps]
    if auto_compress:
        rates += [fps for fps in (25, 20, 10, 5) if fps < options.fps]
    attempt = 0
    for fps in rates:
        try:
            renderer = Renderer(
                calendar,
                fps=fps,
                seed=seed,
                jets=jets,
                carrier=carrier,
                water=water,
                graph_theme=graph_theme,
            )
            scales = (
                range(options.scale, 0, -1)
                if auto_compress and fps == options.fps
                else (1,)
                if auto_compress
                else (options.scale,)
            )
            for scale in scales:
                if attempt:
                    print(
                        f"git-jet: retrying at {WIDTH * scale}x{HEIGHT * scale}, "
                        f"{fps} FPS to fit GIF limits; all day-cell attacks are retained",
                        file=sys.stderr,
                    )
                attempt += 1
                try:
                    return export(
                        renderer,
                        output,
                        Options(scale, fps),
                        source=source,
                        requested_options=options,
                    )
                except GifSizeLimitError:
                    if not auto_compress:
                        raise
        except FrameLimitError:
            if not auto_compress:
                raise
            attempt += 1
    raise GifSizeLimitError(
        "animation cannot fit the GIF limits even at native scale and 5 FPS; select fewer days"
    )
