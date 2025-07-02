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

    TEXT_SIZE_RATIO = 0.02583  # 2.58% of smaller dimension (31pt for 1200px)
    LEADING_RATIO = 1.129  # 112.9% of text size (35pt for 31pt font)
    PADDING_RATIO = 0.03  # 3% of smaller dimension


class DateTimeFormats:
    """Date and time format constants."""

    DATE_FORMAT = "%d-%m-%Y"
    SHORT_DATE_FORMAT = "%y%m%d"
    TIME_FORMAT = "%H:%M"
