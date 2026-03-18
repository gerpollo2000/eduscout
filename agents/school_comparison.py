"""
EduScout School Comparison Agent
Tool for generating side-by-side school comparisons.

Fetches multiple schools from the database and formats them
into a structured comparison the LLM can present to the parent.
"""

import logging
from typing import Optional
from decimal import Decimal

from langchain_core.tools import tool

from tools.database import get_school_by_slug, search_schools

logger = logging.getLogger("eduscout.school_comparison")


def _safe_float(val):
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


def _school_row(school: dict) -> dict:
    """Extract key comparison fields from a school record."""
    tuition = _safe_float(school.get("annual_tuition_max", 0))

    # Special needs
    sn = school.get("special_needs_programs", [])
    sn_list = []
    if isinstance(sn, list):
        for s in sn:
            if isinstance(s, dict):
                sn_list.append(s.get("condition", ""))

    # Extracurriculars
    extras = school.get("extracurriculars", [])
    extra_cats = set()
    if isinstance(extras, list):
        for e in extras:
            if isinstance(e, dict) and e.get("category"):
                extra_cats.add(e["category"])

    # Sports
    sports = school.get("sports", [])
    sport_names = []
    if isinstance(sports, list):
        for s in sports:
            if isinstance(s, dict):
                sport_names.append(s.get("sport", ""))

    return {
        "name": school.get("name", "Unknown"),
        "type": school.get("school_type", "N/A"),
        "level": school.get("level", "N/A"),
        "neighborhood": school.get("neighborhood", "N/A"),
        "tuition": f"${tuition:,.0f}/yr" if tuition > 0 else "Free",
        "class_size": school.get("avg_class_size", "N/A"),
        "methodology": school.get("methodology", "N/A"),
        "wheelchair": "Yes" if school.get("has_wheelchair_access") else "No",
        "elevator": "Yes" if school.get("has_elevator") else "No",
        "special_needs": ", ".join(sn_list) if sn_list else "Not listed",
        "scholarships": "Yes" if school.get("has_scholarships") or school.get("has_financial_aid") else "No",
        "transportation": "Yes" if school.get("has_transportation") else "No",
        "lunch": "Yes" if school.get("has_lunch_program") else "No",
        "extracurriculars": ", ".join(sorted(extra_cats)) if extra_cats else "N/A",
        "sports": ", ".join(sport_names[:5]) if sport_names else "N/A",
        "religious": school.get("religious_orientation", "secular"),
    }


@tool
def compare_schools(
    school_slug_1: str,
    school_slug_2: str,
    school_slug_3: Optional[str] = None,
) -> str:
    """Compare 2 or 3 schools side-by-side.

    Use this when a parent wants to compare specific schools they're
    considering. Returns a structured comparison table.

    Args:
        school_slug_1: Slug of first school (e.g., 'beacon-high-school')
        school_slug_2: Slug of second school (e.g., 'stuyvesant-high-school')
        school_slug_3: Optional slug of third school (e.g., 'ideal-school')
    """
    slugs = [school_slug_1, school_slug_2]
    if school_slug_3:
        slugs.append(school_slug_3)

    schools = []
    not_found = []

    for slug in slugs:
        school = get_school_by_slug(slug)
        if school:
            schools.append(_school_row(school))
        else:
            not_found.append(slug)

    if not schools:
        return f"Could not find any of the requested schools: {', '.join(not_found)}. Use search_schools first to find available schools."

    if not_found:
        output = f"Note: Could not find: {', '.join(not_found)}\n\n"
    else:
        output = ""

    # Build comparison table
    fields = [
        ("Type", "type"),
        ("Level", "level"),
        ("Location", "neighborhood"),
        ("Annual Tuition", "tuition"),
        ("Avg Class Size", "class_size"),
        ("Methodology", "methodology"),
        ("Wheelchair Access", "wheelchair"),
        ("Elevator", "elevator"),
        ("Special Needs Support", "special_needs"),
        ("Scholarships/Aid", "scholarships"),
        ("Transportation", "transportation"),
        ("Lunch Program", "lunch"),
        ("Extracurriculars", "extracurriculars"),
        ("Sports", "sports"),
        ("Religious Orientation", "religious"),
    ]

    # Header
    names = [s["name"] for s in schools]
    output += "SCHOOL COMPARISON\n"
    output += "=" * 60 + "\n\n"

    for label, key in fields:
        output += f"📌 {label}:\n"
        for s in schools:
            output += f"  • {s['name']}: {s.get(key, 'N/A')}\n"
        output += "\n"

    output += "---\n"
    output += "Use this comparison to discuss trade-offs with the parent. "
    output += "Highlight which school best matches their stated preferences."

    return output


# Export
comparison_tools = [compare_schools]
