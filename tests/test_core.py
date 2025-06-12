import pytest
from fastapi.testclient import TestClient
from datetime import time

from liine_gerald_guerreo.main import app, restaurant_service
from liine_gerald_guerreo.parsers import (
    parse_time_string,
    parse_restaurant_hours,
    parse_restaurants_from_csv,
)
from liine_gerald_guerreo.models import TimeRange


@pytest.fixture
def client_with_data():
    """
    Create a test client using mock restaurant data from string variable.
    Uses load function meant for testing environment
    """
    mock_csv = '''\"Restaurant Name\",\"Hours\"
\"Test Restaurant\",\"Mon-Sun 11:00 am - 10 pm\"
\"Weekday Only\",\"Mon-Fri 9 am - 5 pm\"
\"Late Night Spot\",\"Mon-Sun 5 pm - 2 am\"'''
    
    restaurant_service.load_restaurants_from_content(mock_csv)
    return TestClient(app)


class TestCoreAPI:
    """Test the core features of the API needed for the assignment"""
    
    def test_restaurants_open_endpoint_success(self, client_with_data):
        """Test main '/restaurants/open' endpoint to check correct returns structure."""
        response = client_with_data.get("/restaurants/open?datetime=2023-12-25T15:30:00")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify correct response structure is used
        assert "restaurants" in data
        assert isinstance(data["restaurants"], list)
        # There should be restaurants open during business hours
        assert len(data["restaurants"]) > 0
    
    def test_restaurants_open_different_times(self, client_with_data):
        """Test that endpoint returns different results for different times."""
        # Testing during business hours: should have restaurants open
        response_day = client_with_data.get("/restaurants/open?datetime=2023-12-25T15:30:00")
        day_data = response_day.json()
        
        # Testing during early morning: there should be fewer restaurants open
        response_night = client_with_data.get("/restaurants/open?datetime=2023-12-25T03:00:00")
        night_data = response_night.json()
        
        # Should have different results
        assert response_day.status_code == 200
        assert response_night.status_code == 200
        # Checks to ensure business hours have more open restaurants than 3 AM
        assert len(day_data["restaurants"]) >= len(night_data["restaurants"])
    
    def test_invalid_datetime_handling(self, client_with_data):
        """Test to ensure invalid datetime strings are handled correctly."""
        response = client_with_data.get("/restaurants/open?datetime=invalid-date")
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "Invalid datetime format" in data["detail"]
    
    def test_missing_datetime_parameter(self, client_with_data):
        """Test ensures any missing datetime parameter returns validation error."""
        response = client_with_data.get("/restaurants/open")
        assert response.status_code == 422


class TestCoreParser:
    """Test the core parsing functionality"""
    
    def test_parse_simple_hours(self):
        """Test parsing for simple input of restaurant hours."""
        schedule = parse_restaurant_hours("Mon-Sun 11:00 am - 10 pm")
        
        # Should contains all 7 days for schedule
        assert len(schedule) == 7
        for day in range(7):
            assert day in schedule
            assert len(schedule[day].time_ranges) == 1
            assert schedule[day].time_ranges[0].start == time(11, 0)
            assert schedule[day].time_ranges[0].end == time(22, 0)
    
    def test_parse_complex_hours_with_different_schedules(self):
        """Test parsing for complex input with different schedules for different days."""
        schedule = parse_restaurant_hours(
            "Mon-Thu, Sun 11:30 am - 10 pm / Fri-Sat 11:30 am - 11 pm"
        )
        
        # Monday-Thursday and Sunday: 11:30 AM - 10 PM
        weekday_days = [0, 1, 2, 3, 6]  # Mon-Thu, Sun
        for day in weekday_days:
            assert day in schedule
            assert schedule[day].time_ranges[0].end == time(22, 0)
        
        # Friday-Saturday: 11:30 AM - 11 PM  
        weekend_days = [4, 5]  # Fri-Sat
        for day in weekend_days:
            assert day in schedule
            assert schedule[day].time_ranges[0].end == time(23, 0)
    
    def test_parse_overnight_hours(self):
        """Test parsing for hours that go past midnight, needed to fully check schedule"""
        schedule = parse_restaurant_hours("Mon-Wed 5 pm - 2 am")
        
        for day in [0, 1, 2]:  # Mon-Wed
            assert day in schedule
            time_range = schedule[day].time_ranges[0]
            assert time_range.start == time(17, 0)  # 5 PM
            assert time_range.end == time(2, 0)     # 2 AM
    
    def test_overnight_time_logic(self):
        """Test ensures overnight time ranges work as intented."""
        # Create overnight time range: 11 PM - 2 AM
        time_range = TimeRange(start=time(23, 0), end=time(2, 0))
        
        # should be open at 11 PM, midnight, 1 AM, 2 AM
        assert time_range.contains_time(time(23, 0))   # 11 PM
        assert time_range.contains_time(time(0, 0))    # Midnight
        assert time_range.contains_time(time(1, 0))    # 1 AM
        assert time_range.contains_time(time(2, 0))    # 2 AM
        
        # should be closed at 10 PM and 3 AM
        assert not time_range.contains_time(time(22, 0))  # 10 PM
        assert not time_range.contains_time(time(3, 0))   # 3 AM
    
    def test_parse_csv_data(self):
        """Test parsing of the CSV format used in data processing."""
        csv_content = '''\"Restaurant Name\",\"Hours\"
\"Test Restaurant\",\"Mon-Sun 11:00 am - 10 pm\"
\"Another Place\",\"Mon-Fri 9 am - 5 pm\"'''
        
        restaurants = parse_restaurants_from_csv(csv_content)
        
        assert len(restaurants) == 2
        assert restaurants[0].name == "Test Restaurant"
        assert restaurants[1].name == "Another Place"
        
        # Verify parsing results are correct
        assert len(restaurants[0].schedule) == 7  # All days
        assert len(restaurants[1].schedule) == 5  # Weekdays only
    
    def test_time_string_parsing_edge_cases(self):
        """Test parsing of the time strings, including edge cases."""
        # Basic cases
        assert parse_time_string("11 am") == time(11, 0)
        assert parse_time_string("2:30 pm") == time(14, 30)
        
        # Edge cases: midnight and noon
        assert parse_time_string("12 am") == time(0, 0)   # Midnight
        assert parse_time_string("12 pm") == time(12, 0)  # Noon
        
        # Invalid format should raise error
        with pytest.raises(ValueError):
            parse_time_string("invalid")


class TestBusinessLogic:
    """Test rules for closed days in the assignment."""
    
    def test_closed_days_assumption(self):
        """Test that restaurants are closed on unlisted days."""
        # Restaurant only open Mon-Fri
        schedule = parse_restaurant_hours("Mon-Fri 9 am - 5 pm")
        
        # Should have Monday-Friday: 0-4
        assert set(schedule.keys()) == {0, 1, 2, 3, 4}
        
        # Should NOT have Saturday or Sunday: 5-6
        assert 5 not in schedule  # Saturday
        assert 6 not in schedule  # Sunday 