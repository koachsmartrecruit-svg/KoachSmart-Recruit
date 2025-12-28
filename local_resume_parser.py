import re

# =============================
# CONSTANTS
# =============================

SPORTS = [
    "cricket", "football", "tennis", "badminton",
    "basketball", "swimming", "athletics", "hockey"
]

CERTIFICATIONS = [
    "bcci", "aiff", "nsca", "fifa",
    "icc", "afc", "nccp",
    "level one", "level 1",
    "level two", "level 2"
]

SKILL_KEYWORDS = {
    "fitness": "Fitness Training",
    "strength": "Strength & Conditioning",
    "batting": "Batting Technique",
    "bowling": "Bowling Technique",
    "fielding": "Fielding Skills",
    "strategy": "Match Strategy",
    "analysis": "Performance Analysis",
    "discipline": "Discipline & Mentorship",
    "team": "Team Management",
    "nutrition": "Sports Nutrition"
}

WORD_NUMBERS = {
    "one": 1, "two": 2, "three": 3,
    "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8,
    "nine": 9, "ten": 10
}

# =============================
# NORMALIZATION
# =============================

def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace(",", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

# =============================
# EXTRACTION HELPERS
# =============================

def extract_name(text: str) -> str:
    patterns = [
        r"my name is ([a-z ]+?)(?:\.|,|$)",
        r"mera naam ([a-z ]+?) hai",
        r"^([a-z ]+?) i am a",
        r"^([a-z ]+?) i am"
    ]
    for p in patterns:
        match = re.search(p, text)
        if match:
            return match.group(1).title()
    return ""

def extract_sport(text: str) -> str:
    for sport in SPORTS:
        if sport in text:
            return sport.title()
    return ""

def extract_experience_years(text: str) -> int:
    # digit based (5 years)
    match = re.search(r"(\d+)\s+(year|years)", text)
    if match:
        return int(match.group(1))

    # word based (five years)
    for word, num in WORD_NUMBERS.items():
        if f"{word} year" in text or f"{word} years" in text:
            return num

    return 0

def extract_certifications(text: str) -> list:
    certs = []

    # --- BCCI ---
    if "bcci" in text:
        if "level one" in text or "level 1" in text:
            certs.append("BCCI Level One")
        elif "level two" in text or "level 2" in text:
            certs.append("BCCI Level Two")
        else:
            certs.append("BCCI Certified")

    # --- AIFF ---
    if "aiff" in text:
        if "level one" in text or "level 1" in text:
            certs.append("AIFF Level One")
        elif "level two" in text or "level 2" in text:
            certs.append("AIFF Level Two")
        else:
            certs.append("AIFF Certified")

    # --- Other generic certifications ---
    if "nsca" in text:
        certs.append("NSCA Certified")
    if "fifa" in text:
        certs.append("FIFA Certified")

    return certs

def extract_skills(text: str) -> list:
    skills = []
    for key, label in SKILL_KEYWORDS.items():
        if key in text:
            skills.append(label)

    return list(set(skills))

def extract_experience_points(text: str) -> list:
    points = []

    if "under" in text:
        points.append(
            "Trained age-group athletes including Under-14 and Under-16 players."
        )

    if "academy" in text:
        points.append(
            "Conducted structured training sessions at academy level."
        )

    if "school" in text:
        points.append(
            "Provided coaching for school-level sports teams."
        )

    if "fitness" in text:
        points.append(
            "Improved player fitness, stamina, and injury prevention."
        )

    if not points:
        points.append(
            "Delivered structured coaching programs to improve athlete performance."
        )

    return points

def extract_achievements(text: str) -> list:
    achievements = []

    if "district" in text:
        achievements.append(
            "Led teams to district-level tournaments."
        )

    if "state" in text:
        achievements.append(
            "Prepared athletes for state-level competitions."
        )

    if not achievements:
        achievements.append(
            "Consistently improved athlete performance and discipline."
        )

    return achievements

# =============================
# SUMMARY GENERATOR
# =============================

def generate_summary(sport: str, years: int) -> str:
    if not sport:
        sport = "Sports"

    if years > 0:
        return (
            f"Dedicated and results-driven {sport} Coach with over {years} years of "
            f"hands-on experience in athlete development, performance training, "
            f"and competitive preparation."
        )

    return (
        f"Motivated {sport} Coach with practical experience in training athletes, "
        f"improving fitness levels, and building discipline through structured coaching."
    )

# =============================
# MAIN BUILDER
# =============================

def build_resume_from_transcript(transcript: str) -> dict:
    text = normalize(transcript)

    name = extract_name(text)
    sport = extract_sport(text)
    years = extract_experience_years(text)

    # 🔒 NAME SAFETY CLEANUP (IMPORTANT)
    if name and " i am " in name.lower():
        name = name.lower().split(" i am ")[0].title()

    resume = {
        "full_name": name,
        "headline": (
            f"{sport} Coach | {years} Years Experience"
            if sport and years > 0
            else "Professional Coach"
        ),
        "summary": generate_summary(sport, years),
        "skills": extract_skills(text) or [
            "Athlete Development",
            "Fitness Training",
            "Match Strategy"
        ],
        "experience": [
            {
                "role": f"{sport} Coach" if sport else "Coach",
                "description": " ".join(extract_experience_points(text))
            }
        ],
        "certifications": extract_certifications(text),
        "achievements": extract_achievements(text)
    }

    return resume
