#!/usr/bin/env python3
"""Test script to verify date formatting and time increment logic."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'gui'))

from psd_updater.models import TimeInfo, format_date_with_month_name
from psd_updater.constants import DateTimeFormats, Secondhand

def test_date_formatting():
    """Test the date formatting with Indonesian month names."""
    print("=== Testing Date Formatting ===")
    
    test_date = "30/06/2025"
    formatted_date = format_date_with_month_name(test_date)
    
    print(f"Input: {test_date}")
    print(f"Output: {formatted_date}")
    print(f"Expected: 30 Juni 2025")
    print(f"Match: {formatted_date == '30 Juni 2025'}")
    print()

def test_time_increment():
    """Test the time increment logic."""
    print("=== Testing Time Increment Logic ===")
    
    # Create initial time
    time_info = TimeInfo.from_string("13.15.00")
    print(f"Initial: {time_info.formatted}")
    
    # Test increments
    for i in range(4):
        time_info = time_info.increment()
        print(f"After increment {i+1}: {time_info.formatted}")
    
    print()

def test_full_sequence():
    """Test the full sequence as expected."""
    print("=== Testing Full Expected Sequence ===")
    
    date = "30/06/2025"
    formatted_date = format_date_with_month_name(date)
    
    time_info = TimeInfo.from_string("13.15.00")
    
    print(f"File 1: {formatted_date} {time_info.formatted}")
    
    for i in range(3):
        time_info = time_info.increment()
        print(f"File {i+2}: {formatted_date} {time_info.formatted}")

if __name__ == "__main__":
    test_date_formatting()
    test_time_increment()
    test_full_sequence()
