"""Transparent native-grid scene using carrier, jet and effect sprites."""

import math

from PIL import Image, ImageDraw

from .art import (
    CREAM,
    DEFAULT_CARRIER,
    DEFAULT_GRAPH_THEME,
    GOLD,
    carrier_sprite,
    commit_tile,
    explosion_sprite,
    jet_sprite,
    validate_carrier,
    validate_graph_theme,
)
from .calendar import Calendar
from .flight import (
    GRID_STEP,
    GRID_X,
    GRID_Y,
    HEADING_STEPS,
    HEIGHT,
    WIDTH,
    Flight,
    Squadron,
    sprite_heading,
)
from .water import DEFAULT_WATER, validate_water, water_sprite
from .water import POSITION as WATER_POSITION


class Renderer:
    def __init__(
        self,
        calendar: Calendar,
        fps=20,
        seed=None,
        jets=1,
        carrier=DEFAULT_CARRIER,
        water=DEFAULT_WATER,
        graph_theme=DEFAULT_GRAPH_THEME,
    ):
        if type(jets) is not int or not 1 <= jets <= 3:
            raise ValueError("jets must be an integer in 1..3")
        self.jet_count = jets
        self.carrier = validate_carrier(carrier)
        self.water = validate_water(water)
        self.graph_theme = validate_graph_theme(graph_theme)
        self.calendar = calendar
        self.cells = calendar.cells()
        self.flight = (
            Flight(calendar, fps, seed=seed, carrier=self.carrier)
            if jets == 1
            else Squadron(calendar, jets, fps, seed=seed, carrier=self.carrier)
        )
        self.flights = (self.flight,) if jets == 1 else self.flight.flights
        self.frame_count = self.flight.frame_count
        self.maximum = max(day.commits for day in calendar.days)
        self.hit_by_date = {s.cell.day.date: s.hit for s in self.flight.strikes}
        self.jets = {
            (angle, thrust, bank): jet_sprite(angle, thrust, bank)
            for angle in (i * 360 / HEADING_STEPS for i in range(HEADING_STEPS))
            for thrust in range(3)
            for bank in (-1, 0, 1)
        }

    def grid_frame(self, frame_number: int):
        frame = frame_number % self.frame_count
        image = Image.new("RGBA", (WIDTH, HEIGHT))
        for cell in self.cells:
            if cell.day is None:
                continue
            count = cell.day.commits if cell.day else 0
            level = max(1, math.ceil(count / self.maximum * 4)) if count else 0
            hit = self.hit_by_date.get(cell.day.date) if cell.day else None
            cleared = hit is not None and frame >= hit and not self.flight.restored(cell, frame)
            image.alpha_composite(
                commit_tile(level, cleared, theme=self.graph_theme),
                (GRID_X + cell.column * GRID_STEP, GRID_Y + cell.row * GRID_STEP),
            )
        return image

    def jet_image(self, pose, frame):
        angle = sprite_heading(pose.heading)
        thrust = 1 + (frame // 2) % 2 if pose.thrust else 0
        return self.jets[angle, thrust, pose.bank]

    def frame(self, frame_number: int):
        frame = frame_number % self.frame_count
        phase = frame / (self.flight.fps * 4)
        image = Image.new("RGBA", (WIDTH, HEIGHT))
        image.alpha_composite(
            water_sprite(phase, water=self.water, carrier=self.carrier), WATER_POSITION
        )
        image.alpha_composite(carrier_sprite(phase, carrier=self.carrier), (65, 12))
        image.alpha_composite(self.grid_frame(frame))
        draw = ImageDraw.Draw(image)
        for strike in self.flight.strikes:
            if strike.fire <= frame < strike.hit:
                t = (frame - strike.fire) / (strike.hit - strike.fire)
                points = [strike.projectile(max(0, t - offset)) for offset in (0.12, 0.06, 0)]
                draw.line([(round(x), round(y)) for x, y in points], fill=GOLD)
                x, y = points[-1]
                draw.point((round(x), round(y)), fill=CREAM)
            age = (frame - strike.hit) / (0.4 * self.flight.fps)
            if 0 <= age < 1:
                image.alpha_composite(
                    explosion_sprite(age), (strike.target[0] - 12, strike.target[1] - 12)
                )
        for pose in self.flight.visible_poses(frame):
            sprite = self.jet_image(pose, frame)
            half = sprite.width // 2
            image.alpha_composite(sprite, (round(pose.x) - half, round(pose.y) - half))
        return image
