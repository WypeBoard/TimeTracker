"""Unit tests for app.utils helper functions."""
from __future__ import annotations

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.utils import format_hhmm


# ---------------------------------------------------------------------------
# format_hhmm
# ---------------------------------------------------------------------------

class TestFormatHhmm:
    """Tests for the decimal-hours → H:MM clock string converter."""

    @pytest.mark.parametrize("decimal_hours, expected", [
        # Exact whole hours
        (0.0,   "0:00"),
        (1.0,   "1:00"),
        (7.0,   "7:00"),
        (10.0,  "10:00"),
        # Common fractional values
        (0.5,   "0:30"),
        (1.5,   "1:30"),
        (7.4,   "7:24"),   # the project's TARGET_HOURS value
        (7.5,   "7:30"),
        (7.25,  "7:15"),
        (7.75,  "7:45"),
        # Quarter-hour increments
        (0.25,  "0:15"),
        (0.75,  "0:45"),
        # Values larger than 9 hours (double-digit hours, no zero-padding)
        (10.5,  "10:30"),
        (32.5,  "32:30"),  # multi-day totals that exceed 24 h
        # Single-digit minute (zero-padded in minutes column)
        (1.0 + 1/60,  "1:01"),
        (2.0 + 9/60,  "2:09"),
        # Rounding: 0.9917 h = 59.5 min → rounds to 60 min → 1:00
        (0.9917,  "1:00"),
        # Zero
        (0.0,  "0:00"),
    ])
    def test_conversion(self, decimal_hours: float, expected: str) -> None:
        assert format_hhmm(decimal_hours) == expected

    def test_output_contains_colon(self) -> None:
        """Result must always be formatted as H:MM (contains exactly one colon)."""
        result = format_hhmm(5.5)
        assert result.count(":") == 1

    def test_minutes_always_two_digits(self) -> None:
        """The minutes portion must always be zero-padded to two digits."""
        result = format_hhmm(3.0 + 5 / 60)  # 3 h 5 min → "3:05"
        assert result == "3:05"
        _, minutes_part = result.split(":")
        assert len(minutes_part) == 2

    def test_hours_not_zero_padded(self) -> None:
        """Single-digit hours must NOT be zero-padded (e.g. '7:00' not '07:00')."""
        result = format_hhmm(7.0)
        assert result == "7:00"
        assert not result.startswith("0")
