#!/usr/bin/env python3
"""
Location Service - Integration with LocationIQ API
API: https://locationiq.com/
"""
import requests
import os
from flask import current_app
import json

# LocationIQ API Configuration
LOCATIONIQ_API_BASE_URL = "https://us1.locationiq.com/v1"
LOCATIONIQ_API_KEY = os.getenv("LOCATIONIQ_API_KEY", "YOUR_API_KEY_HERE")

# Fallback data for demo/offline mode
FALLBACK_COUNTRIES = [
    {"id": "IN", "name": "India", "iso2": "IN", "iso3": "IND"}
]

FALLBACK_STATES = {
    "IN": [
        {"id": "MH", "name": "Maharashtra", "country_code": "IN"},
        {"id": "KA", "name": "Karnataka", "country_code": "IN"},
        {"id": "TN", "name": "Tamil Nadu", "country_code": "IN"},
        {"id": "GJ", "name": "Gujarat", "country_code": "IN"},
        {"id": "RJ", "name": "Rajasthan", "country_code": "IN"},
        {"id": "UP", "name": "Uttar Pradesh", "country_code": "IN"},
        {"id": "WB", "name": "West Bengal", "country_code": "IN"},
        {"id": "DL", "name": "Delhi", "country_code": "IN"},
        {"id": "PB", "name": "Punjab", "country_code": "IN"},
        {"id": "HR", "name": "Haryana", "country_code": "IN"},
        {"id": "AP", "name": "Andhra Pradesh", "country_code": "IN"},
        {"id": "TS", "name": "Telangana", "country_code": "IN"},
        {"id": "KL", "name": "Kerala", "country_code": "IN"},
        {"id": "OR", "name": "Odisha", "country_code": "IN"},
        {"id": "JH", "name": "Jharkhand", "country_code": "IN"},
        {"id": "AS", "name": "Assam", "country_code": "IN"},
        {"id": "BR", "name": "Bihar", "country_code": "IN"},
        {"id": "CG", "name": "Chhattisgarh", "country_code": "IN"},
        {"id": "GA", "name": "Goa", "country_code": "IN"},
        {"id": "HP", "name": "Himachal Pradesh", "country_code": "IN"}
    ]
}

FALLBACK_CITIES = {
    "MH": [
        {"id": "mumbai", "name": "Mumbai", "state_code": "MH", "lat": "19.0760", "lon": "72.8777"},
        {"id": "pune", "name": "Pune", "state_code": "MH", "lat": "18.5204", "lon": "73.8567"},
        {"id": "nagpur", "name": "Nagpur", "state_code": "MH", "lat": "21.1458", "lon": "79.0882"},
        {"id": "nashik", "name": "Nashik", "state_code": "MH", "lat": "19.9975", "lon": "73.7898"},
        {"id": "aurangabad", "name": "Aurangabad", "state_code": "MH", "lat": "19.8762", "lon": "75.3433"}
    ],
    "KA": [
        {"id": "bangalore", "name": "Bangalore", "state_code": "KA", "lat": "12.9716", "lon": "77.5946"},
        {"id": "mysore", "name": "Mysore", "state_code": "KA", "lat": "12.2958", "lon": "76.6394"},
        {"id": "hubli", "name": "Hubli", "state_code": "KA", "lat": "15.3647", "lon": "75.1240"},
        {"id": "mangalore", "name": "Mangalore", "state_code": "KA", "lat": "12.9141", "lon": "74.8560"}
    ],
    "TN": [
        {"id": "chennai", "name": "Chennai", "state_code": "TN", "lat": "13.0827", "lon": "80.2707"},
        {"id": "coimbatore", "name": "Coimbatore", "state_code": "TN", "lat": "11.0168", "lon": "76.9558"},
        {"id": "madurai", "name": "Madurai", "state_code": "TN", "lat": "9.9252", "lon": "78.1198"},
        {"id": "salem", "name": "Salem", "state_code": "TN", "lat": "11.6643", "lon": "78.1460"}
    ],
    "DL": [
        {"id": "new-delhi", "name": "New Delhi", "state_code": "DL", "lat": "28.6139", "lon": "77.2090"},
        {"id": "south-delhi", "name": "South Delhi", "state_code": "DL", "lat": "28.5355", "lon": "77.2090"},
        {"id": "north-delhi", "name": "North Delhi", "state_code": "DL", "lat": "28.7041", "lon": "77.1025"},
        {"id": "east-delhi", "name": "East Delhi", "state_code": "DL", "lat": "28.6508", "lon": "77.3152"},
        {"id": "west-delhi", "name": "West Delhi", "state_code": "DL", "lat": "28.6692", "lon": "77.1114"}
    ]
}

def get_api_params():
    """Get parameters for LocationIQ API"""
    return {
        "key": LOCATIONIQ_API_KEY,
        "format": "json"
    }

def get_countries():
    """Get list of countries - LocationIQ doesn't have a countries endpoint, so we use fallback"""
    try:
        # LocationIQ doesn't provide a countries list endpoint
        # We'll use our fallback data and focus on India for now
        current_app.logger.info("Using fallback country data (LocationIQ doesn't provide countries endpoint)")
        return {"success": True, "data": FALLBACK_COUNTRIES, "source": "fallback"}
        
    except Exception as e:
        current_app.logger.error(f"Error in get_countries: {str(e)}")
        return {"success": True, "data": FALLBACK_COUNTRIES, "fallback": True}

def get_states(country_code="IN"):
    """Get list of states using LocationIQ search API"""
    try:
        if LOCATIONIQ_API_KEY == "YOUR_API_KEY_HERE":
            # Use fallback data if API key not configured
            current_app.logger.info(f"Using fallback state data for {country_code}")
            return {"success": True, "data": FALLBACK_STATES.get(country_code, []), "source": "fallback"}
        
        # LocationIQ doesn't have a direct states endpoint
        # We'll use search API to get states for India
        if country_code == "IN":
            # Use a combination of search and our fallback data
            # This gives us the best of both worlds
            states_data = []
            
            # Try to get some states via search API
            for state in FALLBACK_STATES["IN"][:5]:  # Test with first 5 states
                try:
                    response = requests.get(
                        f"{LOCATIONIQ_API_BASE_URL}/search.php",
                        params={
                            **get_api_params(),
                            "q": f"{state['name']}, India",
                            "limit": 1,
                            "addressdetails": 1
                        },
                        timeout=3
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data and len(data) > 0:
                            result = data[0]
                            states_data.append({
                                "id": state["id"],
                                "name": state["name"],
                                "country_code": "IN",
                                "lat": result.get("lat"),
                                "lon": result.get("lon"),
                                "verified": True
                            })
                        else:
                            # Add fallback data if API doesn't return results
                            states_data.append(state)
                    else:
                        # Add fallback data if API fails
                        states_data.append(state)
                        
                except Exception as e:
                    # Add fallback data if request fails
                    states_data.append(state)
                    current_app.logger.warning(f"Failed to verify state {state['name']}: {e}")
            
            # Add remaining states from fallback
            for state in FALLBACK_STATES["IN"][5:]:
                states_data.append(state)
            
            current_app.logger.info(f"Retrieved {len(states_data)} states for {country_code}")
            return {"success": True, "data": states_data, "source": "hybrid"}
        else:
            # For other countries, use fallback
            return {"success": True, "data": FALLBACK_STATES.get(country_code, []), "source": "fallback"}
            
    except Exception as e:
        current_app.logger.error(f"Error fetching states for {country_code}: {str(e)}")
        return {"success": True, "data": FALLBACK_STATES.get(country_code, []), "fallback": True}

def get_cities(country_code="IN", state_code="MH"):
    """Get list of cities using LocationIQ search API"""
    try:
        if LOCATIONIQ_API_KEY == "YOUR_API_KEY_HERE":
            # Use fallback data if API key not configured
            current_app.logger.info(f"Using fallback city data for {state_code}")
            return {"success": True, "data": FALLBACK_CITIES.get(state_code, []), "source": "fallback"}
        
        # Get state name for search
        state_name = None
        for state in FALLBACK_STATES.get(country_code, []):
            if state["id"] == state_code:
                state_name = state["name"]
                break
        
        if not state_name:
            return {"success": True, "data": FALLBACK_CITIES.get(state_code, []), "source": "fallback"}
        
        # Use LocationIQ search API to find cities in the state
        try:
            response = requests.get(
                f"{LOCATIONIQ_API_BASE_URL}/search.php",
                params={
                    **get_api_params(),
                    "q": f"city in {state_name}, India",
                    "limit": 50,
                    "addressdetails": 1,
                    "extratags": 1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                cities_data = []
                
                # Process LocationIQ results
                for item in data:
                    if item.get("type") in ["city", "town", "village"] or "city" in item.get("display_name", "").lower():
                        city_name = item.get("display_name", "").split(",")[0].strip()
                        if city_name and len(city_name) > 1:
                            cities_data.append({
                                "id": city_name.lower().replace(" ", "-"),
                                "name": city_name,
                                "state_code": state_code,
                                "lat": item.get("lat"),
                                "lon": item.get("lon"),
                                "verified": True
                            })
                
                # Add fallback cities if we don't have enough
                fallback_cities = FALLBACK_CITIES.get(state_code, [])
                for fallback_city in fallback_cities:
                    if not any(city["name"].lower() == fallback_city["name"].lower() for city in cities_data):
                        cities_data.append(fallback_city)
                
                # Remove duplicates and limit to reasonable number
                seen_names = set()
                unique_cities = []
                for city in cities_data:
                    if city["name"].lower() not in seen_names:
                        seen_names.add(city["name"].lower())
                        unique_cities.append(city)
                        if len(unique_cities) >= 100:  # Limit to 100 cities
                            break
                
                current_app.logger.info(f"Retrieved {len(unique_cities)} cities for {state_code} using LocationIQ")
                return {"success": True, "data": unique_cities, "source": "locationiq"}
            else:
                current_app.logger.warning(f"LocationIQ API error for cities: {response.status_code}")
                return {"success": True, "data": FALLBACK_CITIES.get(state_code, []), "fallback": True}
                
        except Exception as e:
            current_app.logger.error(f"LocationIQ API error: {str(e)}")
            return {"success": True, "data": FALLBACK_CITIES.get(state_code, []), "fallback": True}
            
    except Exception as e:
        current_app.logger.error(f"Error fetching cities for {state_code}: {str(e)}")
        return {"success": True, "data": FALLBACK_CITIES.get(state_code, []), "fallback": True}

def search_cities(query, country_code="IN", limit=10):
    """Search cities by name using LocationIQ"""
    try:
        if LOCATIONIQ_API_KEY == "YOUR_API_KEY_HERE":
            # Use fallback search if API key not configured
            results = []
            query_lower = query.lower()
            
            for state_code, cities in FALLBACK_CITIES.items():
                for city in cities:
                    if query_lower in city["name"].lower():
                        results.append({
                            **city,
                            "state_name": next((s["name"] for s in FALLBACK_STATES["IN"] if s["id"] == state_code), state_code)
                        })
                        if len(results) >= limit:
                            break
                if len(results) >= limit:
                    break
            
            return {"success": True, "data": results, "source": "fallback"}
        
        # Use LocationIQ search API
        try:
            response = requests.get(
                f"{LOCATIONIQ_API_BASE_URL}/search.php",
                params={
                    **get_api_params(),
                    "q": f"{query}, India",
                    "limit": limit,
                    "addressdetails": 1
                },
                timeout=5
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for item in data:
                    if item.get("type") in ["city", "town", "village"]:
                        city_name = item.get("display_name", "").split(",")[0].strip()
                        state_name = None
                        
                        # Extract state from display_name
                        display_parts = item.get("display_name", "").split(",")
                        if len(display_parts) > 1:
                            for part in display_parts:
                                part = part.strip()
                                for state in FALLBACK_STATES["IN"]:
                                    if state["name"].lower() in part.lower():
                                        state_name = state["name"]
                                        break
                                if state_name:
                                    break
                        
                        results.append({
                            "id": city_name.lower().replace(" ", "-"),
                            "name": city_name,
                            "state_name": state_name or "Unknown",
                            "lat": item.get("lat"),
                            "lon": item.get("lon"),
                            "verified": True
                        })
                
                return {"success": True, "data": results, "source": "locationiq"}
            else:
                # Fallback to local search
                return search_cities_fallback(query, limit)
                
        except Exception as e:
            current_app.logger.error(f"LocationIQ search error: {str(e)}")
            return search_cities_fallback(query, limit)
        
    except Exception as e:
        current_app.logger.error(f"Error searching cities: {str(e)}")
        return {"success": False, "data": []}

def search_cities_fallback(query, limit=10):
    """Fallback city search using local data"""
    results = []
    query_lower = query.lower()
    
    for state_code, cities in FALLBACK_CITIES.items():
        for city in cities:
            if query_lower in city["name"].lower():
                results.append({
                    **city,
                    "state_name": next((s["name"] for s in FALLBACK_STATES["IN"] if s["id"] == state_code), state_code)
                })
                if len(results) >= limit:
                    break
        if len(results) >= limit:
            break
    
    return {"success": True, "data": results, "source": "fallback"}

def geocode_address(address):
    """Geocode an address using LocationIQ"""
    try:
        if LOCATIONIQ_API_KEY == "YOUR_API_KEY_HERE":
            return {"success": False, "message": "API key not configured"}
        
        response = requests.get(
            f"{LOCATIONIQ_API_BASE_URL}/search.php",
            params={
                **get_api_params(),
                "q": address,
                "limit": 1,
                "addressdetails": 1
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                return {
                    "success": True,
                    "data": {
                        "lat": result.get("lat"),
                        "lon": result.get("lon"),
                        "display_name": result.get("display_name"),
                        "address": result.get("address", {})
                    }
                }
            else:
                return {"success": False, "message": "No results found"}
        else:
            return {"success": False, "message": f"API error: {response.status_code}"}
            
    except Exception as e:
        current_app.logger.error(f"Geocoding error: {str(e)}")
        return {"success": False, "message": str(e)}

def reverse_geocode(lat, lon):
    """Reverse geocode coordinates using LocationIQ"""
    try:
        if LOCATIONIQ_API_KEY == "YOUR_API_KEY_HERE":
            return {"success": False, "message": "API key not configured"}
        
        response = requests.get(
            f"{LOCATIONIQ_API_BASE_URL}/reverse.php",
            params={
                **get_api_params(),
                "lat": lat,
                "lon": lon,
                "addressdetails": 1
            },
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "data": {
                    "display_name": data.get("display_name"),
                    "address": data.get("address", {})
                }
            }
        else:
            return {"success": False, "message": f"API error: {response.status_code}"}
            
    except Exception as e:
        current_app.logger.error(f"Reverse geocoding error: {str(e)}")
        return {"success": False, "message": str(e)}

def get_location_hierarchy(country_code="IN", state_code=None, city_name=None):
    """Get complete location hierarchy"""
    try:
        result = {
            "country": None,
            "state": None,
            "city": None
        }
        
        # Get country
        countries = get_countries()
        if countries["success"]:
            result["country"] = next((c for c in countries["data"] if c.get("iso2") == country_code), None)
        
        # Get state if provided
        if state_code:
            states = get_states(country_code)
            if states["success"]:
                result["state"] = next((s for s in states["data"] if s.get("id") == state_code), None)
        
        # Get city if provided
        if city_name and state_code:
            cities = get_cities(country_code, state_code)
            if cities["success"]:
                result["city"] = next((c for c in cities["data"] if c.get("name").lower() == city_name.lower()), None)
        
        return {"success": True, "data": result}
        
    except Exception as e:
        current_app.logger.error(f"Error getting location hierarchy: {str(e)}")
        return {"success": False, "data": result}

def validate_location(country_code, state_code, city_name):
    """Validate if a location combination is valid"""
    try:
        hierarchy = get_location_hierarchy(country_code, state_code, city_name)
        
        if not hierarchy["success"]:
            return {"valid": False, "message": "Failed to validate location"}
        
        data = hierarchy["data"]
        
        if not data["country"]:
            return {"valid": False, "message": "Invalid country"}
        
        if state_code and not data["state"]:
            return {"valid": False, "message": "Invalid state"}
        
        if city_name and not data["city"]:
            return {"valid": False, "message": "Invalid city"}
        
        return {
            "valid": True,
            "message": "Location is valid",
            "data": data
        }
        
    except Exception as e:
        current_app.logger.error(f"Error validating location: {str(e)}")
        return {"valid": False, "message": "Validation error"}

# Configuration helper
def configure_api_key(api_key):
    """Configure the API key (call this from app initialization)"""
    global LOCATIONIQ_API_KEY
    LOCATIONIQ_API_KEY = api_key
    current_app.logger.info("LocationIQ API key configured")

def is_api_configured():
    """Check if API is properly configured"""
    return LOCATIONIQ_API_KEY != "YOUR_API_KEY_HERE"