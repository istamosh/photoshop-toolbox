"""Constants for PSD updating functionality."""

from enum import Enum


class LayerKind(Enum):
    """Photoshop layer types."""

    TEXT = 2
    TYPE_17 = 17


class Justification(Enum):
    """Text justification constants."""

    RIGHT = 3


class TextSizing:
    """Text sizing constants."""

    TEXT_SIZE_RATIO = 0.035  # 3.5% of smaller dimension
    LEADING_RATIO = 1.2  # 120% of text size
    PADDING_RATIO = 0.03  # 3% of smaller dimension


class DateTimeFormats:
    """Date and time format constants."""

    DATE_FORMAT = "%d-%m-%Y"
    SHORT_DATE_FORMAT = "%y%m%d"
    TIME_FORMAT = "%H:%M"
