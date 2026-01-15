"""Data models for PSD update functionality."""

import random
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
from .constants import DateTimeFormats, Secondhand


@dataclass
class TimeInfo:
    """Time information for batch processing."""

    hour: int
    minute: int
    second: int = 0

    def increment(self):
        """Increment seconds by randomized gap (10-15 seconds)."""
        # Add randomized seconds gap
        self.second += random.randint(Secondhand.MIN, Secondhand.MAX)
        
        # Handle overflow
        if self.second >= 60:
            extra_minutes = self.second // 60
            self.second = self.second % 60
            self.minute += extra_minutes
            
            if self.minute >= 60:
                extra_hours = self.minute // 60
                self.minute = self.minute % 60
                self.hour = (self.hour + extra_hours) % 24
        
        return self

    @property
    def formatted(self) -> str:
        """Get formatted time string."""
        return f"{self.hour:02d}:{self.minute:02d}:{self.second:02d} WIB"

    @classmethod
    def from_string(cls, time_str: str) -> "TimeInfo":
        """Create TimeInfo from string format (HH.MM or HH.MM.SS)."""
        parts = time_str.split(".")
        hour = int(parts[0])
        minute = int(parts[1])
        
        if len(parts) > 2:
            # If seconds are provided, use them
            second = int(parts[2])
        else:
            # If no seconds provided (old format), start from 00
            # This ensures consistent starting point for batch processing
            second = 0
            
        return cls(hour, minute, second)


@dataclass
class LocationInfo:
    """Structure for location information."""

    street: Optional[str] = None
    ward: Optional[str] = None
    subdistrict: Optional[str] = None
    district: Optional[str] = None
    province: Optional[str] = None
    company: Optional[str] = None

    @property
    def as_list(self) -> List[str]:
        """Get non-empty location fields as list."""
        return [
            field
            for field in [
                self.street,
                self.ward,
                self.subdistrict,
                self.district,
                self.province,
                self.company,
            ]
            if field
        ]

    @classmethod
    def from_text(cls, text: str) -> "LocationInfo":
        """Create LocationInfo from multiline text."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        fields = lines + [None] * (6 - len(lines))  # Pad with None if needed
        return cls(*fields[:6])  # Only take first 6 fields


def format_date_with_month_name(date_str: str) -> str:
    """Convert date from DD/MM/YYYY or DD-MM-YYYY to 'DD Month YYYY' format."""
    try:
        # Handle both "/" and "-" separators
        if "/" in date_str:
            day, month, year = date_str.split("/")
        elif "-" in date_str:
            day, month, year = date_str.split("-")
        else:
            # If it's already in the correct format, return as-is
            return date_str

        day = int(day)
        month = int(month)
        year = int(year)

        month_name = DateTimeFormats.MONTH_NAMES.get(month, "Unknown")
        return f"{day:02d} {month_name} {year}"
    except (ValueError, KeyError):
        # If parsing fails, return original string
        return date_str
