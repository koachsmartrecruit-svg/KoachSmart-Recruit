import re

# ===============================
# CONSTANT MAPS
# ===============================

SPORT_MAP = {
    "फुटबॉल": "Football",
    "football": "Football",
    "क्रिकेट": "Cricket",
    "cricket": "Cricket",
    "बैडमिंटन": "Badminton",
    "badminton": "Badminton",
    "हॉकी": "Hockey",
    "hockey": "Hockey",
}

SKILL_MAP = {
    "फिटनेस": "Fitness Training",
    "fitness": "Fitness Training",
    "अनुशासन": "Discipline Building",
    "discipline": "Discipline Building",
    "प्रशिक्षण": "Athlete Development",
    "training": "Athlete Development",
    "रणनीति": "Match Strategy",
    "strategy": "Match Strategy",
}

# ===============================
# MAIN PARSER
# ===============================

def parse_resume_text(text: str):
    warnings = []
    score = 0

    text = text.strip()
    text_lower = text.lower()

    # ---------------------------
    # NAME
    # ---------------------------
    name = "Professional Coach"

    hi_name = re.search(r"मेरा नाम (.+?) है", text)
    en_name = re.search(r"my name is ([a-zA-Z\s]+)", text_lower)

    if hi_name:
        name = hi_name.group(1).strip()
        score += 20
    elif en_name:
        name = en_name.group(1).strip().title()
        score += 20
    else:
        warnings.append("Name not clearly mentioned.")

    # ---------------------------
    # SPORT
    # ---------------------------
    sport = "Sports"
    for k, v in SPORT_MAP.items():
        if k.lower() in text_lower:
            sport = v
            score += 20
            break
    if sport == "Sports":
        warnings.append("Sport not clearly detected.")

    # ---------------------------
    # EXPERIENCE
    # ---------------------------
    experience = "0"

    hi_exp = re.search(r"(\d+)\s*साल", text)
    en_exp = re.search(r"(\d+)\s*years", text_lower)

    if hi_exp:
        experience = hi_exp.group(1)
        score += 20
    elif en_exp:
        experience = en_exp.group(1)
        score += 20
    else:
        warnings.append("Experience not mentioned in years.")

    # ---------------------------
    # AGE GROUP
    # ---------------------------
    age_groups = []
    if "under 14" in text_lower or "अंडर 14" in text:
        age_groups.append("Under-14")
        score += 5
    if "under 16" in text_lower or "अंडर 16" in text:
        age_groups.append("Under-16")
        score += 5

    # ---------------------------
    # SKILLS
    # ---------------------------
    skills = set()
    for k, v in SKILL_MAP.items():
        if k.lower() in text_lower:
            skills.add(v)

    if skills:
        score += 15
    else:
        warnings.append("Skills not clearly mentioned.")
        skills = {"Athlete Development", "Fitness Training"}

    # ---------------------------
    # CERTIFICATIONS
    # ---------------------------
    certifications = []

    if "aiff" in text_lower or "एआईएफएफ" in text:
        certifications.append("AIFF")
    if "bcci" in text_lower or "बीसीसीआई" in text:
        certifications.append("BCCI")
    if (
        "level one" in text_lower
        or "level 1" in text_lower
        or "लेवल वन" in text
    ):
        certifications.append("Level One")

    final_certs = []
    if "AIFF" in certifications and "Level One" in certifications:
        final_certs.append("AIFF Level One")
        score += 10
    if "BCCI" in certifications and "Level One" in certifications:
        final_certs.append("BCCI Level One")
        score += 10

    if not final_certs:
        warnings.append("Certifications not clearly detected.")
        final_certs = ["Not specified"]

    # ---------------------------
    # SUMMARY
    # ---------------------------
    summary = (
        f"Motivated {sport} Coach with over {experience} years of practical "
        f"experience in athlete development, fitness training, and discipline-based coaching."
    )

    # ---------------------------
    # EXPERIENCE SECTION
    # ---------------------------
    experience_section = [{
        "role": f"{sport} Coach",
        "description": (
            "Delivered structured coaching programs"
            + (f" for {', '.join(age_groups)} athletes." if age_groups else ".")
        )
    }]

    # ---------------------------
    # ACHIEVEMENTS
    # ---------------------------
    achievements = [
        "Consistently improved athlete performance and discipline."
    ]

    # ---------------------------
    # CONFIDENCE SCORE CLAMP
    # ---------------------------
    confidence_score = min(score, 100)

    return {
        "full_name": name,
        "headline": f"{sport} Coach | {experience} Years Experience",
        "summary": summary,
        "skills": list(skills),
        "experience": experience_section,
        "certifications": final_certs,
        "achievements": achievements,
        "confidence_score": confidence_score,
        "warnings": warnings
    }
