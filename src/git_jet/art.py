"""Owner-approved Lincoln and Classic carriers, jets, radar and effects."""

import math

from PIL import Image, ImageDraw

INK = "#142736"
NAVY = "#203748"
STEEL = "#526b77"
LIGHT = "#9bbdcb"
CREAM = "#f4e6c8"
SHADE = "#c9bea6"
GOLD = "#efbe5d"
RED = "#a34e44"
WAVE = "#70b3ce"
DEEP = "#39799c"
FOAM = "#f1f4e8"
GRID = ("#244252", "#28556d", "#39799c", "#70b3ce", "#bfe6eb")
GITHUB_GRID = ("#30363d", "#0e4429", "#006d32", "#26a641", "#39d353")
DEFAULT_GRAPH_THEME = "blue"
GRAPH_THEMES = ("blue", "github")
DEFAULT_CARRIER = "lincoln"
CARRIERS = ("lincoln", "classic")


def validate_graph_theme(graph_theme):
    if not isinstance(graph_theme, str) or graph_theme not in GRAPH_THEMES:
        raise ValueError("graph theme must be blue or github")
    return graph_theme


def validate_carrier(carrier):
    if not isinstance(carrier, str) or carrier not in CARRIERS:
        raise ValueError("carrier must be lincoln or classic")
    return carrier


def carrier_launch_points(carrier=DEFAULT_CARRIER):
    validate_carrier(carrier)
    if carrier == "classic":
        # Keep the 55-pixel landing roll on the deck, with room for a queue
        # on either side of the central launch/parking position.
        return (168, 33, 28), (-8, 32, 28)
    from .lincoln import flight_anchors

    return flight_anchors()


def carrier_radar_origin(carrier=DEFAULT_CARRIER):
    validate_carrier(carrier)
    if carrier == "classic":
        return 185, 10, 60
    from .lincoln import RADAR_ORIGIN

    return RADAR_ORIGIN


def project(u, v, z=0):
    return round(35 + 0.94 * u + 0.76 * v), round(140 - 0.29 * u + 0.30 * v - z)


def jet_sprite(heading=0, thrust=0, bank=0):
    image = Image.new("RGBA", (37, 37))
    draw = ImageDraw.Draw(image)
    cx, top = 18, 3

    def points(vertices):
        return [(cx + x, top + y) for x, y in vertices]

    if thrust:
        length = 3 + thrust * 2
        draw.polygon(points([(-2, 24), (0, 24 + length), (2, 24)]), fill=RED)
        draw.polygon(points([(-1, 24), (0, 23 + length), (1, 24)]), fill=GOLD)
        draw.line((cx, top + 24, cx, top + 26), fill=CREAM)
    left = -8 if bank >= 0 else -5
    right = 8 if bank <= 0 else 5
    outline = [
        (0, 0),
        (2, 5),
        (2, 10),
        (right, 16),
        (right, 18),
        (2, 16),
        (2, 21),
        (5, 24),
        (5, 25),
        (0, 23),
        (-5, 25),
        (-5, 24),
        (-2, 21),
        (-2, 16),
        (left, 18),
        (left, 16),
        (-2, 10),
        (-2, 5),
    ]
    draw.polygon(points(outline), fill=INK)
    draw.polygon(points([(0, 2), (1, 6), (1, 21), (0, 23), (-1, 21), (-1, 6)]), fill=CREAM)
    draw.polygon(points([(-2, 12), (left + 1, 16), (left + 1, 17), (-1, 15)]), fill=LIGHT)
    draw.polygon(points([(2, 12), (right - 1, 16), (right - 1, 17), (1, 15)]), fill=STEEL)
    draw.line(points([(0, 3), (0, 5)]), fill=FOAM)
    draw.rectangle((cx - 1, top + 7, cx + 1, top + 11), fill=DEEP)
    draw.line((cx - 1, top + 7, cx - 1, top + 10), fill=WAVE)
    draw.point((cx, top + 13), fill=GOLD)
    draw.line(points([(-3, 23), (-1, 22)]), fill=LIGHT)
    draw.line(points([(3, 23), (1, 22)]), fill=SHADE)
    return image.rotate(-heading, resample=Image.Resampling.NEAREST)


def radar_sprite(t=0):
    """Turn the existing mast antenna around its spindle once per scene cycle."""
    image = Image.new("RGBA", (16, 11))
    angle = math.tau * (t % 1)
    dx, dy = 5.5 * math.cos(angle), 2.5 * math.sin(angle)
    # Foreshortening and the shaded back face make the whole turn readable.
    vertices = [
        (round(7.5 - dx), round(5 - dy - 1)),
        (round(7.5 + dx), round(5 + dy - 1)),
        (round(7.5 + dx), round(5 + dy + 1)),
        (round(7.5 - dx), round(5 - dy + 1)),
    ]
    ImageDraw.Draw(image).polygon(vertices, fill=CREAM if math.cos(angle) >= 0 else LIGHT)
    return image


def carrier_sprite(t=0, *, carrier=DEFAULT_CARRIER):
    validate_carrier(carrier)
    if carrier == "classic":
        return classic_carrier_sprite(t)
    from .lincoln import carrier_sprite as lincoln_carrier

    return lincoln_carrier(t)


def classic_carrier_sprite(t=0):
    image = Image.new("RGBA", (350, 190))
    draw = ImageDraw.Draw(image)

    def poly(vertices, color):
        draw.polygon([project(*vertex) for vertex in vertices], fill=color)

    def line(vertices, color, width=1):
        draw.line([project(*vertex) for vertex in vertices], fill=color, width=width)

    def block(u, v, w, depth, z, height):
        poly([(u, v, z), (u + w, v, z), (u + w, v, z + height), (u, v, z + height)], STEEL)
        poly([(u, v, z), (u, v + depth, z), (u, v + depth, z + height), (u, v, z + height)], SHADE)
        poly(
            [
                (u, v + depth, z),
                (u + w, v + depth, z),
                (u + w, v + depth, z + height),
                (u, v + depth, z + height),
            ],
            LIGHT,
        )
        poly(
            [
                (u, v, z + height),
                (u + w, v, z + height),
                (u + w, v + depth, z + height),
                (u, v + depth, z + height),
            ],
            CREAM,
        )

    # Deep sidewalls, red waterline, and angular bow face in the reference view.
    poly([(-18, 20, 24), (-18, 36, 24), (8, 52, 24), (8, 52, 0), (-18, 36, 0), (-18, 20, 7)], INK)
    poly(
        [(-17, 24, 22), (-17, 35, 22), (8, 50, 22), (8, 50, 3), (-17, 35, 3), (-17, 24, 9)],
        "#33546a",
    )
    poly([(8, 52, 24), (256, 52, 24), (256, 52, 1), (8, 52, 0)], INK)
    poly([(10, 52, 22), (254, 52, 22), (254, 52, 4), (10, 52, 3)], NAVY)
    poly([(10, 52, 4), (254, 52, 5), (249, 52, 1), (12, 52, 0)], RED)
    line([(12, 52, 0), (249, 52, 1)], "#813b3c")
    for u in range(28, 235, 24):
        line([(u, 52, 17), (u + 12, 52, 17)], "#33546a", 2)
        line([(u + 3, 52, 10), (u + 8, 52, 10)], INK)
    # Stern face and stern deck rim.
    poly([(256, 12, 24), (256, 52, 24), (256, 52, 1), (256, 12, 5)], STEEL)
    deck = [
        (-18, 20, 24),
        (0, 0, 24),
        (248, 0, 24),
        (256, 12, 24),
        (256, 52, 24),
        (8, 52, 24),
        (-18, 36, 24),
    ]
    poly(deck, INK)
    poly(
        [
            (-14, 20, 25),
            (1, 2, 25),
            (246, 2, 25),
            (253, 13, 25),
            (253, 49, 25),
            (9, 49, 25),
            (-14, 35, 25),
        ],
        STEEL,
    )
    line([(-14, 20, 25), (1, 2, 25), (246, 2, 25), (253, 13, 25)], LIGHT)
    line([(9, 49, 25), (253, 49, 25)], LIGHT)
    # Deck plate seams and tie-down crosses stay outside the landing strip.
    for u in range(22, 246, 16):
        for v in (5, 10, 47):
            x, y = project(u, v, 26)
            draw.point((x, y), fill=LIGHT)
            draw.point((x - 1, y + 1), fill="#354f5e")
    for u in (40, 88, 136, 216):
        line([(u, 2, 26), (u, 17, 26)], "#425d6c")
    # Starboard safety net and individually stepped catwalk stanchions.
    line([(14, 53, 22), (247, 53, 22)], "#697b88")
    for u in range(15, 248, 11):
        line([(u, 53, 22), (u, 53, 25)], LIGHT)
    for u in range(222, 250, 5):
        line([(u, 4, 26), (u + 3, 10, 26)], GOLD)

    # Long angled runway, catapult lanes and dashed centre markings.
    poly([(-5, 20, 26), (247, 24, 26), (247, 45, 26), (0, 40, 26)], "#354f5e")
    line([(-5, 20, 26), (247, 24, 26)], CREAM)
    line([(0, 40, 26), (247, 45, 26)], CREAM)
    line([(0, 24, 26), (245, 28, 26)], LIGHT)
    for u in range(12, 237, 23):
        v = 31 + u / 247 * 3
        line([(u, v, 26), (u + 11, v + 0.2, 26)], SHADE)
    line([(12, 14, 26), (150, 14, 26)], GOLD)
    line([(36, 44, 26), (239, 47, 26)], GOLD)
    for v in (23, 27, 31, 35):
        line([(2, v, 26), (15, v, 26)], CREAM)
    for u in (195, 203, 211):
        line([(u, 24, 26), (u, 44, 26)], LIGHT)
    # Arrestor cables, deck-edge lamps, and projected runway number 07.
    for u in (170, 180, 190):
        line([(u, 22, 27), (u + 3, 43, 27)], INK)
    for u in range(16, 244, 18):
        draw.point(project(u, 40 + u / 247 * 5, 27), fill=GOLD)
    digits = ((7, 5, 5, 5, 7), (7, 1, 2, 2, 2))
    for digit, rows in enumerate(digits):
        for row, bits in enumerate(rows):
            for col in range(3):
                if bits & (1 << (2 - col)):
                    u, v = 22 + (4 - row) * 2, 23 + digit * 9 + col * 2
                    poly([(u, v, 27), (u + 2, v, 27), (u + 2, v + 2, 27), (u, v + 2, 27)], CREAM)
    # Small recessed hangars and lifeboats along the near side.
    for u in (87, 128, 169, 210):
        poly([(u, 52, 17), (u + 22, 52, 17), (u + 22, 52, 8), (u, 52, 8)], INK)
        line([(u + 2, 52, 16), (u + 19, 52, 16)], LIGHT)
        line([(u + 4, 52, 9), (u + 17, 52, 9)], STEEL)
        line([(u + 5, 52, 10), (u + 5, 52, 14)], "#33546a")
        line([(u + 12, 52, 10), (u + 12, 52, 14)], "#33546a")
    for u in (51, 61, 71, 238, 244):
        line([(u, 52, 16), (u + 3, 52, 16)], LIGHT)
    # Recessed elevator outline and a deck-edge service platform.
    poly([(131, 43, 26), (155, 43, 26), (155, 51, 26), (131, 51, 26)], INK)
    poly([(133, 44, 27), (153, 44, 27), (153, 50, 27), (133, 50, 27)], STEEL)
    line([(133, 44, 27), (153, 44, 27)], GOLD)
    for u in (134, 141, 148):
        line([(u, 52, 11), (u + 4, 52, 16)], LIGHT)
    for u in (112, 185):
        line([(u, 53, 13), (u + 13, 53, 13)], "#d9825b", 2)
        line([(u + 3, 53, 14), (u + 10, 53, 14)], CREAM)
        draw.point(project(u + 3, 53, 13), fill=INK)
        draw.point(project(u + 9, 53, 13), fill=INK)

    # Bow anchor and a short hanging chain on the illuminated face.
    x, y = project(-17, 30, 12)
    draw.line((x, y - 4, x, y + 3), fill=INK)
    draw.line((x - 2, y, x + 2, y), fill=INK)
    draw.line((x - 2, y + 1, x, y + 3, x + 2, y + 1), fill=INK)

    # Parked air wing is projected onto the deck, with separate wings and canopies.
    for u, v in ((49, 9), (78, 9), (108, 9), (219, 12), (241, 13)):
        silhouette = [
            (-11, 0),
            (-5, -2),
            (0, -2),
            (6, -9),
            (8, -9),
            (4, -2),
            (10, -2),
            (13, -5),
            (13, -3),
            (11, 0),
            (13, 3),
            (13, 5),
            (10, 2),
            (4, 2),
            (8, 9),
            (6, 9),
            (0, 2),
            (-5, 2),
        ]
        poly([(u + a, v + b, 28) for a, b in silhouette], INK)
        line([(u - 9, v, 29), (u + 10, v, 29)], CREAM, 2)
        line([(u, v - 2, 29), (u + 6, v - 7, 29)], LIGHT, 2)
        line([(u, v + 2, 29), (u + 6, v + 7, 29)], LIGHT, 2)
        line([(u - 4, v, 30), (u - 1, v, 30)], DEEP, 2)
        draw.point(project(u + 8, v, 30), fill=GOLD)

    # A tiny tow tractor and crew pixels provide scale beside the island.
    poly([(132, 6, 28), (140, 6, 28), (140, 12, 28), (132, 12, 28)], GOLD)
    line([(135, 8, 29), (138, 8, 29)], INK, 2)
    for u, v in ((125, 15), (144, 8), (201, 14)):
        x, y = project(u, v, 28)
        draw.point((x, y - 1), fill=CREAM)
        draw.point((x, y), fill=RED)

    # Stepped ivory island, blue bridge windows and a compact radar mast.
    block(159, 3, 34, 16, 26, 10)
    block(166, 5, 28, 14, 36, 13)
    block(171, 4, 25, 17, 49, 8)
    for u in (174, 180, 186, 192):
        line([(u, 21, 55), (u + 3, 21, 55)], INK, 2)
        line([(u, 21, 55), (u + 2, 21, 55)], WAVE)
    block(175, 6, 18, 12, 57, 3)
    # Island side windows, ledges, access door and ventilated panels.
    for u in (168, 174, 180, 186, 192):
        line([(u, 19, 43), (u + 2, 19, 43)], INK)
        line([(u, 19, 39), (u + 2, 19, 39)], DEEP)
    line([(164, 20, 35), (194, 20, 35)], INK)
    line([(164, 20, 36), (194, 20, 36)], CREAM)
    line([(165, 19, 28), (165, 19, 33)], INK, 2)
    for u in (174, 180, 186):
        line([(u, 19, 30), (u + 2, 19, 30)], STEEL)
        line([(u, 19, 32), (u + 2, 19, 32)], STEEL)
    for u in (173, 179, 185, 191):
        line([(u, 21, 49), (u, 21, 51)], LIGHT)
    line([(172, 21, 51), (195, 21, 51)], CREAM)
    x, y = project(176, 12, 62)
    draw.ellipse((x - 3, y - 3, x + 2, y + 1), fill=LIGHT)
    draw.line((x - 2, y - 3, x, y - 3), fill=CREAM)
    x, y = project(185, 10, 60)
    draw.line((x, y, x, y - 22), fill=INK, width=2)
    draw.line((x + 1, y - 2, x + 1, y - 20), fill=LIGHT)
    draw.line((x - 9, y - 12, x + 8, y - 12), fill=SHADE)
    image.alpha_composite(radar_sprite(t), (x - 7, y - 23))
    draw.line((x + 6, y - 9, x + 6, y - 15), fill=LIGHT)
    draw.line((x - 7, y - 4, x + 7, y - 4), fill=STEEL)
    draw.line((x - 6, y - 4, x - 3, y - 9), fill=LIGHT)
    draw.line((x + 6, y - 4, x + 3, y - 9), fill=LIGHT)
    # Two small aerials near the bow are below the flight path.
    for u, v in ((-5, 6), (20, 50)):
        x, y = project(u, v, 26)
        draw.line((x, y, x, y - 7), fill=LIGHT)
        draw.point((x, y - 8), fill=GOLD)
    return image


def commit_tile(level, destroyed=False, *, theme=DEFAULT_GRAPH_THEME):
    validate_graph_theme(theme)
    image = Image.new("RGBA", (7, 7))
    draw = ImageDraw.Draw(image)
    outline = [(1, 0), (5, 0), (6, 1), (6, 5), (5, 6), (1, 6), (0, 5), (0, 1)]
    if theme == "github":
        # Flat green activity squares with neutral, transparent empty cells.
        active = level and not destroyed
        draw.polygon(outline, fill=GITHUB_GRID[min(4, level)] if active else GITHUB_GRID[0])
        if not active:
            draw.rectangle((1, 1, 5, 5), fill=(0, 0, 0, 0))
        return image
    draw.polygon(outline, fill=GRID[0])
    if level and not destroyed:
        draw.rectangle((1, 1, 5, 5), fill=GRID[min(4, level)])
        draw.line((1, 1, 4, 1), fill=LIGHT if level < 3 else FOAM)
    else:
        draw.rectangle((1, 1, 5, 5), fill=(0, 0, 0, 0))
    return image


def explosion_sprite(age):
    image = Image.new("RGBA", (25, 25))
    draw = ImageDraw.Draw(image)
    if not 0 <= age < 1:
        return image
    radius = max(1, round(2 + math.sin(age * math.pi) * 6))
    cx, cy = 12, 12
    if age < 0.68:
        draw.polygon(
            [
                (cx - radius, cy - 2),
                (cx - 3, cy - 3),
                (cx, cy - radius),
                (cx + 2, cy - 3),
                (cx + radius, cy),
                (cx + 3, cy + 3),
                (cx, cy + radius),
                (cx - 2, cy + 3),
            ],
            fill=RED,
        )
        draw.rectangle((cx - radius + 2, cy - 2, cx + radius - 2, cy + 2), fill=GOLD)
        draw.rectangle((cx - 2, cy - radius + 2, cx + 2, cy + radius - 2), fill=GOLD)
        draw.rectangle((cx - 1, cy - 1, cx + 1, cy + 1), fill=FOAM)
    else:
        for dx, dy in ((-4, -2), (3, -4), (0, 3)):
            draw.rectangle((cx + dx, cy + dy, cx + dx + 2, cy + dy + 1), fill=STEEL)
    for index in range(5):
        angle = index * math.tau / 5 + 0.3
        reach = round(3 + age * 8)
        x = cx + round(math.cos(angle) * reach)
        y = cy + round(math.sin(angle) * reach)
        draw.point((x, y), fill=GOLD if age < 0.7 else LIGHT)
    return image
