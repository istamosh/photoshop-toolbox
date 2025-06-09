"""Data models for PSD update functionality."""

from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class TimeInfo:
    """Time information for batch processing."""

    hour: int
    minute: int

    def increment(self):
        """Increment time by one minute."""
        self.minute += 1
        if self.minute >= 60:
            self.hour = (self.hour + 1) % 24
            self.minute = 0
        return self

    @property
    def formatted(self) -> str:
        """Get formatted time string."""
        return f"{self.hour:02d}.{self.minute:02d}"

    @classmethod
    def from_string(cls, time_str: str) -> "TimeInfo":
        """Create TimeInfo from string format (HH.MM)."""
        hour, minute = map(int, time_str.split("."))
        return cls(hour, minute)


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
