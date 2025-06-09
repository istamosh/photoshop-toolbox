"""Location storage and retrieval using YAML."""

import os
from pathlib import Path
import yaml
from typing import List, Dict, Optional


class LocationStorage:
    """Handle location data storage and retrieval using YAML."""

    def __init__(self):
        """Initialize location storage."""
        # Store in the project's data directory
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.yaml_file = self.data_dir / "locations.yaml"
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        """Create the YAML file if it doesn't exist."""
        if not self.yaml_file.exists():
            self.save_locations([])

    def load_locations(self) -> List[Dict[str, str]]:
        """Load all locations from the YAML file."""
        try:
            with open(self.yaml_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or []
        except Exception:
            return []

    def save_locations(self, locations: List[Dict[str, str]]):
        """Save locations to the YAML file."""
        with open(self.yaml_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(locations, f, allow_unicode=True, sort_keys=False)

    def add_location(self, location_text: str) -> bool:
        """Add a new location if it doesn't exist."""
        # Split the text into lines and remove empty lines
        lines = [line.strip() for line in location_text.split("\n") if line.strip()]
        if not lines:
            return False

        # Create location dictionary
        fields = ["street", "ward", "subdistrict", "district", "province", "company"]
        location = {}
        for i, field in enumerate(fields):
            if i < len(lines):
                location[field] = lines[i]
            else:
                location[field] = ""

        # Load existing locations
        locations = self.load_locations()

        # Check if location already exists
        if location not in locations:
            locations.append(location)
            self.save_locations(locations)
            return True
        return False

    def search_locations(self, query: str) -> List[Dict[str, str]]:
        """Search for locations containing the given text."""
        query = query.lower()
        locations = self.load_locations()
        matches = []

        for location in locations:
            # Search in all fields
            if any(query in str(value).lower() for value in location.values()):
                matches.append(location)

        return matches

    def format_location(self, location: Dict[str, str]) -> str:
        """Format a location dictionary as a string."""
        return "\n".join(str(value) for value in location.values() if value)
