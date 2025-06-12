"""
Main service used for handling restaurant data.

Module containes the business logic for loading and providing processed restaurant data.
"""

import os
from dateutil import parser as date_parser
from .parsers import parse_restaurants_from_csv


class RestaurantService:
    """Manages all data and query logic for retreiving restaurant data"""
    
    def __init__(self):
        """Initialize RestaurantService class with no data by default"""
        self._restaurants = []
        self._loaded = False
    
    def load_restaurants_from_csv(self, csv_file_path: str) -> None:
        """
        Load restaurant data from a given CSV file.
        """
        if not os.path.exists(csv_file_path):
            raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
        
        with open(csv_file_path, 'r', encoding='utf-8') as file:
            csv_content = file.read()
        
        self._restaurants = parse_restaurants_from_csv(csv_content)
        self._loaded = True
        
        print(f"Loaded {len(self._restaurants)} restaurants from {csv_file_path}")
    
    def load_restaurants_from_content(self, csv_content: str) -> None:
        """
        Load restaurant data from CSV text using raw text in place of filename (meant for testing).
        """
        self._restaurants = parse_restaurants_from_csv(csv_content)
        self._loaded = True
        
        print(f"Loaded {len(self._restaurants)} restaurants from content")
    
    def is_loaded(self) -> bool:
        """Check if restaurant data is loaded."""
        return self._loaded
    
    def get_restaurant_count(self) -> int:
        """Return total number of loaded restaurants."""
        return len(self._restaurants)
    
    def get_all_restaurants(self):
        """Return all loaded restaurants."""
        return self._restaurants.copy()
    
    def find_open_restaurants(self, datetime_str: str):
        """
        Main logic that finds restaurants that are open at a specific time based on input.
        
        Takes in datetime_str, A DateTime string that can be in various formats such as 
        ISO or human-readable
            
        Returns a list of restaurant names that are open at the given time input
            
        Raises ValueError if the datetime string cannot be parsed or a RuntimeError 
        if restaurant data is not loaded
        """
        if not self._loaded:
            raise RuntimeError("Restaurant data not loaded. Call load_restaurants_from_csv first.")
        
        # Parse the datetime string using dateutil
        try:
            query_datetime = date_parser.parse(datetime_str)
        except Exception as e:
            raise ValueError(f"Invalid datetime format: {datetime_str}") from e
        
        # Find open restaurants
        open_restaurants = []
        for restaurant in self._restaurants:
            if restaurant.is_open_at_datetime(query_datetime):
                open_restaurants.append(restaurant.name)
        
        return sorted(open_restaurants)  # Return sorted for consistency
    
    def get_restaurant_by_name(self, name: str):
        """
        Finds and returns a restaurant by name, not case sensitive.
        """
        for restaurant in self._restaurants:
            if restaurant.name.lower() == name.lower():
                return restaurant
        return None
    
    def get_restaurants_open_on_day(self, weekday: int):
        """
        Returns all restaurants that are open on a specific day.
        
        0=Monday, ... 6=Sunday
        """
        if not 0 <= weekday <= 6:
            raise ValueError("Weekday must be between 0 (Monday) and 6 (Sunday)")
        
        if not self._loaded:
            raise RuntimeError("Restaurant data not loaded. Call load_restaurants_from_csv first.")
        
        open_restaurants = []
        for restaurant in self._restaurants:
            if weekday in restaurant.schedule:
                open_restaurants.append(restaurant.name)
        
        return sorted(open_restaurants) 