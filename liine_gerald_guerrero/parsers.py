"""
Parsers retrieve restaurant hours from text.

Functions are used to parse restaurant hours
from strings into structured data
"""

import csv
import re
from datetime import time
from io import StringIO

from .models import Restaurant, DaySchedule, TimeRange


def parse_time_string(time_str: str) -> time:
    """
    Convert time input from string, like "11:30 am", into a proper time object.
    
    Handles edge cases, "12 am" (midnight) and "12 pm" (noon), correctly.
    """
    time_str = time_str.strip().lower()
    
    # Handle edge cases for midnight and noon
    if time_str in ('12 am', '12:00 am'):
        return time(0, 0)
    elif time_str in ('12 pm', '12:00 pm'):
        return time(12, 0)
    
    # Regular time parsing
    time_pattern = r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)'
    match = re.match(time_pattern, time_str)
    
    if not match:
        raise ValueError(f"Cannot parse time string: {time_str}")
    
    hour = int(match.group(1))
    minute = int(match.group(2)) if match.group(2) else 0
    am_pm = match.group(3)
    
    # Convert to 24-hour format
    if am_pm == 'pm' and hour != 12:
        hour += 12
    elif am_pm == 'am' and hour == 12:
        hour = 0
    
    try:
        return time(hour, minute)
    except ValueError as e:
        raise ValueError(f"Invalid time: {time_str}") from e


def parse_day_range(day_str: str):
    """
    Parse a day range by mapping day strings to weekday integers.
    
    Returns a list of weekday numbers (0=Monday, ..., 6=Sunday).
    """
    day_mapping = {
        'mon': 0, 'tue': 1, 'tues': 1, 'wed': 2, 'thu': 3, 'thurs': 3,
        'fri': 4, 'sat': 5, 'sun': 6
    }
    
    day_str = day_str.strip().lower()
    days = []
    
    # Handle comma-separated days
    for part in day_str.split(','):
        part = part.strip()
        
        if '-' in part:
            # Day range (e.g., "Mon-Fri")
            start_day, end_day = part.split('-', 1)
            start_day = start_day.strip()
            end_day = end_day.strip()
            
            if start_day not in day_mapping or end_day not in day_mapping:
                raise ValueError(f"Unknown day in range: {part}")
            
            start_idx = day_mapping[start_day]
            end_idx = day_mapping[end_day]
            
            # Handle week wraparound (e.g., "Sat-Mon")
            if start_idx <= end_idx:
                days.extend(range(start_idx, end_idx + 1))
            else:
                days.extend(range(start_idx, 7))
                days.extend(range(0, end_idx + 1))
        else:
            # Single day
            if part not in day_mapping:
                raise ValueError(f"Unknown day: {part}")
            days.append(day_mapping[part])
    
    return sorted(list(set(days)))


def parse_time_range(time_range_str: str):
    """
    Parse a time range from a string input into a proper TimeRange object.

    """
    if '-' not in time_range_str:
        raise ValueError(f"No time range separator found: {time_range_str}")
    
    start_str, end_str = time_range_str.split('-', 1)
    start_time = parse_time_string(start_str.strip())
    end_time = parse_time_string(end_str.strip())
    
    return TimeRange(start=start_time, end=end_time)


def parse_restaurant_hours(hours_str: str):
    """
    Parse restaurant hours from day and time range data into a schedule dictionary.
    
    """
    schedule = {}
    
    # Split by '/' to handle multiple time periods
    time_periods = [period.strip() for period in hours_str.split('/')]
    
    for period in time_periods:
        period = period.strip()
        if not period:
            continue
            
        # Find the time range part (everything after the last comma or beginning)
        # Look for pattern: days, time_range
        parts = period.rsplit(' ', 3)  # Split from right to get last 3 parts (time range)
        
        if len(parts) < 4:
            raise ValueError(f"Cannot parse time period: {period}")
        
        days_part = ' '.join(parts[:-3])
        time_range_part = ' '.join(parts[-3:])
        
        try:
            days = parse_day_range(days_part)
            time_range = parse_time_range(time_range_part)
        except ValueError:
            # Try alternative parsing, used format might not be consistent
            # Looks for pattern where time starts with digit
            match = re.search(r'(\d{1,2}(?::\d{2})?\s*(?:am|pm))', period, re.IGNORECASE)
            if not match:
                raise ValueError(f"Cannot find time in period: {period}")
            
            time_start_pos = match.start()
            days_part = period[:time_start_pos].strip()
            time_range_part = period[time_start_pos:].strip()
            
            days = parse_day_range(days_part)
            time_range = parse_time_range(time_range_part)
        
        # Adds current time range to each day
        for day in days:
            if day not in schedule:
                schedule[day] = DaySchedule()
            schedule[day].time_ranges.append(time_range)
    
    return schedule


def parse_restaurants_from_csv(csv_content: str):
    """
    Read restaurant data from CSV file and parse the opening hours.
    
    Skips any restaurants that can't be parsed without stopping.
    """
    restaurants = []
    
    # Uses Python's csv module for CSV parsing
    csv_reader = csv.reader(StringIO(csv_content))
    
    # Skip header line
    try:
        next(csv_reader)
    except StopIteration:
        return restaurants  # Empty file
    
    for row in csv_reader:
        # Skip empty or malformed rows
        if len(row) != 2:
            continue
            
        name, hours = row
        
        try:
            schedule = parse_restaurant_hours(hours)
            restaurant = Restaurant(name=name, schedule=schedule)
            restaurants.append(restaurant)
        except ValueError as e:
            # Log the error but continue processing other restaurants
            print(f"Warning: Could not parse hours for {name}: {e}")
            continue
    
    return restaurants 