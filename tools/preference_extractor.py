"""
EduScout Preference Extractor (Day 8)
Server-side extraction of parent preferences from message text.

This runs in the webhook BEFORE calling the agent, guaranteeing that
interests, special_needs, methodology, and wheelchair preferences
get saved to the DB even if the LLM forgets to call update_search_session.

This is NOT AI — it's simple keyword matching. Fast, deterministic, reliable.
"""

import re
import logging
from typing import Optional

logger = logging.getLogger("eduscout.preference_extractor")

# ============================================================
# KEYWORD MAPS
# ============================================================

SPECIAL_NEEDS_KEYWORDS = {
    "adhd": ["adhd", "attention deficit", "add ", "attention disorder"],
    "autism": ["autism", "autistic", "asd", "spectrum", "asperger"],
    "dyslexia": ["dyslexia", "dyslexic", "reading disorder", "reading difficulty"],
    "wheelchair": ["wheelchair", "wheel chair", "mobility", "paralysis", "paralyzed"],
    "down_syndrome": ["down syndrome", "down's syndrome", "downs"],
    "speech": ["speech disorder", "speech therapy", "speech delay", "stuttering", "stutter"],
    "hearing": ["hearing impaired", "deaf", "hearing loss", "hard of hearing"],
    "vision": ["visually impaired", "blind", "low vision", "vision loss"],
    "anxiety": ["anxiety disorder", "social anxiety", "severe anxiety"],
    "sensory": ["sensory processing", "sensory disorder", "sensory issues"],
}

INTEREST_KEYWORDS = {
    "theater": ["theater", "theatre", "drama", "acting", "stagecraft", "musical"],
    "music": ["music", "band", "orchestra", "choir", "piano", "violin", "guitar", "instrument"],
    "art": ["art ", "arts ", "painting", "drawing", "sculpture", "visual art"],
    "robotics": ["robotics", "robots", "robot"],
    "stem": ["stem", "science", "engineering", "technology"],
    "coding": ["coding", "programming", "computer science", "code"],
    "basketball": ["basketball"],
    "soccer": ["soccer", "futbol", "fútbol"],
    "swimming": ["swimming", "swim team"],
    "dance": ["dance", "dancing", "ballet"],
    "debate": ["debate", "speech and debate", "model un", "mun"],
    "chess": ["chess"],
    "writing": ["creative writing", "journalism", "newspaper", "literary"],
    "sports": ["sports", "athletics", "athletic"],
    "math": ["math team", "math competition", "math olympiad", "mathematics competition"],
    "film": ["film", "filmmaking", "video production"],
}

METHODOLOGY_KEYWORDS = {
    "montessori": ["montessori"],
    "waldorf": ["waldorf", "steiner"],
    "progressive": ["progressive education", "progressive school", "progressive approach"],
    "traditional": ["traditional education", "traditional school", "structured curriculum"],
    "IB": ["international baccalaureate", " ib ", " ib,", "ib program"],
    "stem_focus": ["stem focused", "stem-focused", "stem school", "stem program"],
    "portfolio": ["portfolio-based", "portfolio based", "project-based", "project based"],
    "religious": ["religious education", "faith-based", "faith based"],
}

LEVEL_KEYWORDS = {
    "elementary": ["elementary", "primary", "grade school", "pre-k", "prek", "kindergarten", "k-5", "grades 1", "grades 2", "grades 3", "grades 4", "grades 5"],
    "middle": ["middle school", "junior high", "6th grade", "7th grade", "8th grade", "grades 6", "grades 7", "grades 8"],
    "high": ["high school", "9th grade", "10th grade", "11th grade", "12th grade", "grades 9", "secondary"],
    "k12": ["k-12", "k12", "all grades"],
}

NEIGHBORHOOD_KEYWORDS = {
    "Upper East Side": ["upper east side", "ues", "east side"],
    "Upper West Side": ["upper west side", "uws", "west side"],
    "Chelsea": ["chelsea"],
    "Harlem": ["harlem"],
    "Midtown": ["midtown"],
    "Tribeca": ["tribeca"],
    "SoHo": ["soho"],
    "Greenwich Village": ["greenwich village", "village", "west village"],
    "Lower East Side": ["lower east side", "les"],
    "Financial District": ["financial district", "fidi", "wall street"],
    "East Village": ["east village"],
    "Murray Hill": ["murray hill"],
    "Gramercy": ["gramercy"],
    "Hell's Kitchen": ["hell's kitchen", "hells kitchen", "clinton"],
    "Washington Heights": ["washington heights"],
    "Inwood": ["inwood"],
    "Lincoln Square": ["lincoln square", "lincoln center"],
}


def extract_preferences(text: str) -> dict:
    """
    Extract school preferences from a parent's message.
    Returns dict of detected preferences (only non-empty fields).
    
    This is called by the webhook on EVERY message to catch
    what the LLM might miss.
    """
    text_lower = text.lower()
    result = {}

    # Special needs
    needs = []
    for need, keywords in SPECIAL_NEEDS_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                needs.append(need)
                break
    if needs:
        result["special_needs"] = ",".join(needs)

    # Wheelchair (also set boolean)
    if "wheelchair" in needs:
        result["needs_wheelchair_access"] = True
    elif any(kw in text_lower for kw in ["wheelchair", "wheel chair", "wheelchair access"]):
        result["needs_wheelchair_access"] = True

    # Interests
    interests = []
    for interest, keywords in INTEREST_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                interests.append(interest)
                break
    if interests:
        result["interests"] = ",".join(interests)

    # Methodology
    for method, keywords in METHODOLOGY_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                result["preferred_methodology"] = method
                break
        if "preferred_methodology" in result:
            break

    # Level
    for level, keywords in LEVEL_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                result["target_level"] = level
                break
        if "target_level" in result:
            break

    # Budget extraction
    budget_match = re.search(
        r'(?:budget|afford|spend|pay|tuition|cost).*?(?:\$|usd\s*)?([\d,]+(?:\.\d+)?)\s*(?:k|thousand|per year|/year|/yr|a year)?',
        text_lower
    )
    if budget_match:
        amount_str = budget_match.group(1).replace(",", "")
        try:
            amount = float(amount_str)
            if amount < 1000:
                amount *= 1000  # "40k" → 40000
            result["budget_max"] = amount
        except ValueError:
            pass

    # Also check simpler patterns like "$40000" or "$40,000"
    if "budget_max" not in result:
        money_match = re.search(r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:k|thousand)?', text_lower)
        if money_match:
            amount_str = money_match.group(1).replace(",", "")
            try:
                amount = float(amount_str)
                if amount < 1000:
                    amount *= 1000
                result["budget_max"] = amount
            except ValueError:
                pass

    # Free/public school check
    if any(phrase in text_lower for phrase in ["free school", "public school", "no tuition", "free option", "public only", "charter school"]):
        result["budget_max"] = 0

    # Neighborhood
    for hood, keywords in NEIGHBORHOOD_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                result["preferred_neighborhood"] = hood
                break
        if "preferred_neighborhood" in result:
            break

    # Religious
    religious_map = {
        "catholic": ["catholic", "catholicism"],
        "jewish": ["jewish", "judaism", "hebrew"],
        "episcopal": ["episcopal"],
        "quaker": ["quaker", "friends school"],
        "islamic": ["islamic", "muslim"],
        "secular": ["secular", "non-religious", "no religion"],
    }
    for religion, keywords in religious_map.items():
        for kw in keywords:
            if kw in text_lower:
                result["religious_preference"] = religion
                break
        if "religious_preference" in result:
            break

    if result:
        logger.info(f"[extractor] Extracted from message: {result}")

    return result


def merge_preferences(existing: dict, new: dict) -> dict:
    """
    Merge new preferences into existing ones.
    For comma-separated fields (special_needs, interests), append unique values.
    For other fields, new values override existing.
    """
    merged = dict(existing)

    for key, value in new.items():
        if key in ("special_needs", "interests") and merged.get(key):
            # Append unique values
            existing_set = set(merged[key].split(","))
            new_set = set(value.split(","))
            combined = existing_set | new_set
            merged[key] = ",".join(sorted(combined))
        else:
            merged[key] = value

    return merged
