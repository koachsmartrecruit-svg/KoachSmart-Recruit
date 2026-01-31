import os
import requests
import json
from flask import current_app

def calculate_match_score(profile, job):
    score = 0
    reasons = []

    if profile.sport == job.sport:
        score += 40
        reasons.append("Matching sport")

    if profile.city == job.city:
        score += 20
        reasons.append("Same city")

    if profile.experience_years:
        try:
            exp_years = int(profile.experience_years)
            if exp_years >= 2:
                score += 20
                reasons.append("Sufficient experience")
        except (ValueError, TypeError):
            # Handle case where experience_years is not a valid number
            pass

    if profile.certifications:
        score += 20
        reasons.append("Has certifications")

    return score, ", ".join(reasons)


def predict_salary(title, sport, city, state, country, job_type, requirements=None):
    """
    Use AI to predict salary range for a coaching position
    """
    try:
        api_key = os.getenv('OPENROUTER_API_KEY')
        if not api_key:
            return None, "AI service not configured"
        
        # Build location string
        location_parts = [part for part in [city, state, country] if part]
        location = ", ".join(location_parts) if location_parts else "India"
        
        # Create prompt for salary prediction
        prompt = f"""
You are a sports industry salary expert in India. Predict a realistic monthly salary range for this coaching position:

Position: {title}
Sport: {sport}
Location: {location}
Job Type: {job_type}
Requirements: {requirements or 'Standard coaching requirements'}

Consider these factors:
- Indian sports coaching market rates
- Location cost of living
- Sport popularity and demand
- Job type (Full Time, Part Time, etc.)
- Experience requirements

Provide ONLY a salary range in this exact format: "25000 - 40000"
No currency symbols, no explanations, just the numbers with a dash.
"""

        # Make API call to OpenRouter
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "meta-llama/llama-3.2-3b-instruct:free",  # Free model
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 50,
                "temperature": 0.3
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and len(data['choices']) > 0:
                predicted_range = data['choices'][0]['message']['content'].strip()
                
                # Validate the format (should be like "25000 - 40000")
                if ' - ' in predicted_range and predicted_range.replace(' - ', '').replace(' ', '').isdigit():
                    # Generate reasoning
                    reasoning = generate_salary_reasoning(title, sport, location, job_type)
                    return predicted_range, reasoning
                else:
                    # Fallback to rule-based prediction
                    return rule_based_salary_prediction(sport, location, job_type)
            else:
                return rule_based_salary_prediction(sport, location, job_type)
        else:
            current_app.logger.error(f"OpenRouter API error: {response.status_code}")
            return rule_based_salary_prediction(sport, location, job_type)
            
    except Exception as e:
        current_app.logger.error(f"Salary prediction error: {str(e)}")
        return rule_based_salary_prediction(sport, location, job_type)


def rule_based_salary_prediction(sport, location, job_type):
    """
    Fallback rule-based salary prediction when AI is not available
    """
    # Base salary ranges by sport popularity in India
    sport_multipliers = {
        'cricket': 1.3,
        'football': 1.2,
        'basketball': 1.1,
        'badminton': 1.2,
        'tennis': 1.1,
        'swimming': 1.0,
        'athletics': 1.0,
        'volleyball': 0.9,
        'hockey': 1.0,
        'table tennis': 0.9,
        'boxing': 0.9,
        'wrestling': 0.9,
        'kabaddi': 1.1,
        'kho kho': 0.8,
        'chess': 0.8
    }
    
    # Location multipliers (rough cost of living)
    location_multipliers = {
        'mumbai': 1.4,
        'delhi': 1.3,
        'bangalore': 1.2,
        'bengaluru': 1.2,
        'pune': 1.1,
        'hyderabad': 1.1,
        'chennai': 1.1,
        'kolkata': 1.0,
        'ahmedabad': 1.0,
        'surat': 0.9,
        'jaipur': 0.9,
        'lucknow': 0.8,
        'kanpur': 0.8,
        'nagpur': 0.8,
        'indore': 0.8,
        'bhopal': 0.8,
        'visakhapatnam': 0.8,
        'patna': 0.7,
        'vadodara': 0.9,
        'ghaziabad': 1.0,
        'ludhiana': 0.9,
        'agra': 0.8,
        'nashik': 0.9,
        'faridabad': 1.0,
        'meerut': 0.8,
        'rajkot': 0.9,
        'kalyan-dombivali': 1.2,
        'vasai-virar': 1.1,
        'varanasi': 0.7,
        'srinagar': 0.7,
        'aurangabad': 0.8,
        'dhanbad': 0.7,
        'amritsar': 0.8,
        'navi mumbai': 1.3,
        'allahabad': 0.7,
        'ranchi': 0.7,
        'howrah': 0.9,
        'coimbatore': 0.9,
        'jabalpur': 0.7,
        'gwalior': 0.7,
        'vijayawada': 0.8,
        'jodhpur': 0.8,
        'madurai': 0.8,
        'raipur': 0.7,
        'kota': 0.8,
        'guwahati': 0.8,
        'chandigarh': 1.1,
        'solapur': 0.8,
        'hubli-dharwad': 0.8,
        'tiruchirappalli': 0.8,
        'bareilly': 0.7,
        'mysore': 0.8,
        'tiruppur': 0.8,
        'gurgaon': 1.2,
        'aligarh': 0.7,
        'jalandhar': 0.8,
        'bhubaneswar': 0.8,
        'salem': 0.8,
        'mira-bhayandar': 1.2,
        'warangal': 0.8,
        'thiruvananthapuram': 0.9,
        'guntur': 0.8,
        'bhiwandi': 1.1,
        'saharanpur': 0.7,
        'gorakhpur': 0.7,
        'bikaner': 0.7,
        'amravati': 0.8,
        'noida': 1.1,
        'jamshedpur': 0.8,
        'bhilai': 0.7,
        'cuttack': 0.7,
        'firozabad': 0.7,
        'kochi': 0.9,
        'nellore': 0.8,
        'bhavnagar': 0.8,
        'dehradun': 0.9,
        'durgapur': 0.8,
        'asansol': 0.8,
        'rourkela': 0.8,
        'nanded': 0.7,
        'kolhapur': 0.8,
        'ajmer': 0.7,
        'akola': 0.7,
        'gulbarga': 0.7,
        'jamnagar': 0.8,
        'ujjain': 0.7,
        'loni': 1.0,
        'siliguri': 0.8,
        'jhansi': 0.7,
        'ulhasnagar': 1.1,
        'jammu': 0.8,
        'sangli-miraj & kupwad': 0.8,
        'mangalore': 0.9,
        'erode': 0.8,
        'belgaum': 0.8,
        'ambattur': 1.0,
        'tirunelveli': 0.8,
        'malegaon': 0.7,
        'gaya': 0.6,
        'jalgaon': 0.7,
        'udaipur': 0.8,
        'maheshtala': 0.9
    }
    
    # Job type multipliers
    job_type_multipliers = {
        'full time': 1.0,
        'part time': 0.6,
        'contract': 0.8,
        'internship': 0.4
    }
    
    # Base salary range (monthly in INR)
    base_min = 20000
    base_max = 35000
    
    # Apply multipliers
    sport_mult = sport_multipliers.get(sport.lower(), 1.0)
    location_mult = location_multipliers.get(location.lower(), 0.9) if location else 0.9
    job_type_mult = job_type_multipliers.get(job_type.lower(), 1.0)
    
    # Calculate final range
    final_min = int(base_min * sport_mult * location_mult * job_type_mult)
    final_max = int(base_max * sport_mult * location_mult * job_type_mult)
    
    # Ensure minimum viable salary
    final_min = max(final_min, 15000)
    final_max = max(final_max, final_min + 10000)
    
    predicted_range = f"{final_min} - {final_max}"
    reasoning = f"Based on {sport} coaching demand, {location or 'location'} market rates, and {job_type} position requirements"
    
    return predicted_range, reasoning


def generate_salary_reasoning(title, sport, location, job_type):
    """Generate human-readable reasoning for salary prediction"""
    reasons = []
    
    if sport.lower() in ['cricket', 'football', 'badminton']:
        reasons.append(f"{sport} is a popular sport with good demand")
    
    if location and location.lower() in ['mumbai', 'delhi', 'bangalore', 'bengaluru', 'pune']:
        reasons.append(f"{location} is a major city with higher coaching rates")
    
    if job_type.lower() == 'full time':
        reasons.append("Full-time position offers stable income")
    elif job_type.lower() == 'part time':
        reasons.append("Part-time position with flexible hours")
    
    if not reasons:
        reasons.append("Based on current Indian sports coaching market trends")
    
    return ". ".join(reasons) + "."
