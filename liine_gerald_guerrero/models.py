"""
Basic data models for restaurant hours.

Simple classes to represent restaurants, schedules, and time ranges.
"""

from datetime import datetime, time
from pydantic import BaseModel


class TimeRange(BaseModel):
    """A time range like 9am-5pm."""
    start: time
    end: time
    
    def contains_time(self, check_time: time) -> bool:
        """
        Check if a given time falls within this time range.
        
        Handles overnight edge cases like 11pm-2am too.
        """
        if self.start <= self.end:
            # Normal range (e.g., 9:00 AM - 5:00 PM)
            return self.start <= check_time <= self.end
        else:
            # Overnight range (e.g., 11:00 PM - 2:00 AM)
            return check_time >= self.start or check_time <= self.end


class DaySchedule(BaseModel):
    """What times a place is open on one day."""
    time_ranges: list = []
    
    def is_open_at_time(self, check_time: time) -> bool:
        """
        Check if open at given time
        """
        return any(time_range.contains_time(check_time) for time_range in self.time_ranges)


class Restaurant(BaseModel):
    """A restaurant with its name and weekly hours."""
    name: str
    schedule: dict = {}  # Maps weekday (0-6) to DaySchedule
    
    def is_open_at_datetime(self, dt: datetime) -> bool:
        """
        Check if the restaurant is open at a specific time.

        """
        weekday = dt.weekday()  # 0 = Monday, 6 = Sunday
        
        if weekday not in self.schedule:
            return False
        
        day_schedule = self.schedule[weekday]
        return day_schedule.is_open_at_time(dt.time()) 