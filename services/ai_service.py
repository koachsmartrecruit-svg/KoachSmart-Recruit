def calculate_match_score(profile, job):
    score = 0
    reasons = []

    if profile.sport == job.sport:
        score += 40
        reasons.append("Matching sport")

    if profile.city == job.city:
        score += 20
        reasons.append("Same city")

    if profile.experience_years and profile.experience_years >= 2:
        score += 20
        reasons.append("Sufficient experience")

    if profile.certifications:
        score += 20
        reasons.append("Has certifications")

    return score, ", ".join(reasons)
