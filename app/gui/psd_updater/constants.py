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

    TEXT_SIZE_RATIO = 0.05  # 5% of smaller dimension (31pt for 1200px)
    LEADING_RATIO = 1.129  # 112.9% of text size (35pt for 31pt font)
    PADDING_RATIO = 0.01  # 1% of smaller dimension


class DateTimeFormats:
    """Date and time format constants."""

    DATE_FORMAT = "%d-%m-%Y"
    SHORT_DATE_FORMAT = "%y%m%d"
    TIME_FORMAT = "%H:%M"
    FULL_DATE_FORMAT = "%d %B %Y"  # dd Month yyyy format
    
    # Month names mapping
    MONTH_NAMES = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "Mei", 6: "Jun", 7: "Jul", 8: "Agu", 
        9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"
    }

class Secondhand:
    """Declaring the gap time between batch photos"""
    MIN = 30
    MAX = 120