"""Explicitly synthetic, deterministic offline example calendar."""

from datetime import date, timedelta

from .calendar import make_calendar


def demo_calendar(days=365):
    end = date(2026, 11, 1)
    counts = {
        end - timedelta(days=days): (index % 7) + 1
        for index, days in enumerate(
            (
                350,
                320,
                123,
                234,
                230,
                233,
                212,
                241,
                200,
                201,
                202,
                203,
                204,
                99,
                100,
                100,
                292,
                270,
                230,
                203,
                175,
                151,
                122,
                90,
                61,
                32,
                14,
                2,
            )
        )
    }
    return make_calendar("git-jet", end, days, counts)
