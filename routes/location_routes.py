#!/usr/bin/env python3
"""
Location API Routes - Dynamic Country/State/City dropdowns with LocationIQ
"""
from flask import Blueprint, jsonify, request
from services.location_service import (
    get_countries, get_states, get_cities, search_cities, 
    validate_location, geocode_address, reverse_geocode
)

# ---------------------------
# Blueprint
# ---------------------------
location_bp = Blueprint("location", __name__)

# ---------------------------
# API Routes
# ---------------------------

@location_bp.route("/api/countries", methods=["GET"])
def api_countries():
    """Get list of countries"""
    try:
        result = get_countries()
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to fetch countries",
            "error": str(e)
        }), 500

@location_bp.route("/api/states", methods=["GET"])
def api_states():
    """Get list of states for a country"""
    try:
        country_code = request.args.get('country', 'IN')
        result = get_states(country_code)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to fetch states",
            "error": str(e)
        }), 500

@location_bp.route("/api/cities", methods=["GET"])
def api_cities():
    """Get list of cities for a state"""
    try:
        country_code = request.args.get('country', 'IN')
        state_code = request.args.get('state')
        
        if not state_code:
            return jsonify({
                "success": False,
                "message": "State code is required"
            }), 400
        
        result = get_cities(country_code, state_code)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to fetch cities",
            "error": str(e)
        }), 500

@location_bp.route("/api/cities/search", methods=["GET"])
def api_search_cities():
    """Search cities by name"""
    try:
        query = request.args.get('q', '').strip()
        country_code = request.args.get('country', 'IN')
        limit = int(request.args.get('limit', 10))
        
        if not query or len(query) < 2:
            return jsonify({
                "success": False,
                "message": "Query must be at least 2 characters"
            }), 400
        
        result = search_cities(query, country_code, limit)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to search cities",
            "error": str(e)
        }), 500

@location_bp.route("/api/validate", methods=["POST"])
def api_validate_location():
    """Validate location combination"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "success": False,
                "message": "JSON data required"
            }), 400
        
        country_code = data.get('country', 'IN')
        state_code = data.get('state')
        city_name = data.get('city')
        
        result = validate_location(country_code, state_code, city_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to validate location",
            "error": str(e)
        }), 500

# ---------------------------
# LocationIQ Specific Routes
# ---------------------------

@location_bp.route("/api/geocode", methods=["GET"])
def api_geocode():
    """Geocode an address using LocationIQ"""
    try:
        address = request.args.get('address', '').strip()
        
        if not address:
            return jsonify({
                "success": False,
                "message": "Address parameter is required"
            }), 400
        
        result = geocode_address(address)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to geocode address",
            "error": str(e)
        }), 500

@location_bp.route("/api/reverse-geocode", methods=["GET"])
def api_reverse_geocode():
    """Reverse geocode coordinates using LocationIQ"""
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({
                "success": False,
                "message": "Both lat and lon parameters are required"
            }), 400
        
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return jsonify({
                "success": False,
                "message": "Invalid latitude or longitude format"
            }), 400
        
        result = reverse_geocode(lat, lon)
        return jsonify(result)
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to reverse geocode coordinates",
            "error": str(e)
        }), 500

# ---------------------------
# Demo/Test Routes
# ---------------------------

@location_bp.route("/api/location/demo", methods=["GET"])
def api_demo_data():
    """Get demo location data for testing"""
    try:
        demo_data = {
            "countries": [{"id": "IN", "name": "India", "iso2": "IN"}],
            "popular_states": [
                {"id": "MH", "name": "Maharashtra"},
                {"id": "KA", "name": "Karnataka"},
                {"id": "TN", "name": "Tamil Nadu"},
                {"id": "DL", "name": "Delhi"},
                {"id": "GJ", "name": "Gujarat"}
            ],
            "popular_cities": [
                {"name": "Mumbai", "state": "Maharashtra", "lat": "19.0760", "lon": "72.8777"},
                {"name": "Bangalore", "state": "Karnataka", "lat": "12.9716", "lon": "77.5946"},
                {"name": "Chennai", "state": "Tamil Nadu", "lat": "13.0827", "lon": "80.2707"},
                {"name": "Delhi", "state": "Delhi", "lat": "28.6139", "lon": "77.2090"},
                {"name": "Pune", "state": "Maharashtra", "lat": "18.5204", "lon": "73.8567"}
            ],
            "api_info": {
                "provider": "LocationIQ",
                "features": ["Geocoding", "Reverse Geocoding", "Search", "Address Details"],
                "website": "https://locationiq.com/"
            }
        }
        
        return jsonify({
            "success": True,
            "data": demo_data,
            "message": "Demo location data with LocationIQ integration"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to get demo data",
            "error": str(e)
        }), 500

@location_bp.route("/api/location/status", methods=["GET"])
def api_status():
    """Get LocationIQ API status"""
    try:
        from services.location_service import is_api_configured, LOCATIONIQ_API_KEY
        
        status = {
            "api_configured": is_api_configured(),
            "api_provider": "LocationIQ",
            "api_url": "https://locationiq.com/",
            "features": {
                "countries": "Fallback data (India focus)",
                "states": "Hybrid (LocationIQ + Fallback)",
                "cities": "LocationIQ Search API",
                "geocoding": "LocationIQ Geocoding API",
                "reverse_geocoding": "LocationIQ Reverse API",
                "search": "LocationIQ Search API"
            }
        }
        
        if is_api_configured():
            status["api_key_status"] = "Configured"
            status["api_key_preview"] = f"{LOCATIONIQ_API_KEY[:8]}...{LOCATIONIQ_API_KEY[-4:]}"
        else:
            status["api_key_status"] = "Not configured"
            status["message"] = "Add LOCATIONIQ_API_KEY to environment variables"
        
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to get API status",
            "error": str(e)
        }), 500