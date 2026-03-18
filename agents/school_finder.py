"""
EduScout School Finder Agent
LangChain tools for searching and retrieving school data from PostgreSQL.

These tools are bound to the LLM via LangGraph's tool calling mechanism.
The LLM decides WHEN to call them and with WHAT parameters based on the
parent's conversation.
"""

import json
import logging
from typing import Optional
from decimal import Decimal

from langchain_core.tools import tool

from tools.database import search_schools, get_school_by_slug

logger = logging.getLogger("eduscout.school_finder")


def _serialize(obj):
    """Handle Decimal and other non-JSON types from PostgreSQL."""
    if isinstance(obj, Decimal):
        return float(obj)
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    return str(obj)


def _format_school_summary(school: dict) -> str:
    """Format a school record into a readable summary for the LLM."""
    tuition = school.get("annual_tuition_max", 0) or 0
    tuition_str = f"${tuition:,.0f}/year" if tuition > 0 else "Free (public)"

    parts = [
        f"**{school['name']}**",
        f"  Type: {school.get('school_type', 'N/A')} | Level: {school.get('level', 'N/A')}",
        f"  Location: {school.get('neighborhood', 'Manhattan')}, {school.get('address', 'N/A')}",
        f"  Tuition: {tuition_str}",
        f"  Class size: {school.get('avg_class_size', 'N/A')} students",
    ]

    # Accessibility
    access = []
    if school.get("has_wheelchair_access"):
        access.append("wheelchair accessible")
    if school.get("has_elevator"):
        access.append("elevator")
    if school.get("has_sensory_friendly_spaces"):
        access.append("sensory-friendly spaces")
    if access:
        parts.append(f"  Accessibility: {', '.join(access)}")

    # Special needs
    if school.get("has_special_needs_support"):
        sn = school.get("special_needs_programs", [])
        if isinstance(sn, list) and sn:
            conditions = [s.get("condition", "") for s in sn if isinstance(s, dict)]
            if conditions:
                parts.append(f"  Special needs support: {', '.join(conditions)}")
        else:
            parts.append("  Special needs support: Yes")

    # Key features
    features = []
    if school.get("has_scholarships") or school.get("has_financial_aid"):
        features.append("scholarships/financial aid available")
    if school.get("has_transportation"):
        features.append("transportation provided")
    if school.get("has_lunch_program"):
        features.append("lunch program")
    if school.get("methodology"):
        features.append(f"methodology: {school['methodology']}")
    if school.get("religious_orientation") and school["religious_orientation"] != "secular":
        features.append(f"religious: {school['religious_orientation']}")
    if features:
        parts.append(f"  Features: {', '.join(features)}")

    # Extracurriculars
    extras = school.get("extracurriculars", [])
    if isinstance(extras, list) and extras:
        categories = set()
        for e in extras:
            if isinstance(e, dict) and e.get("category"):
                categories.add(e["category"])
        if categories:
            parts.append(f"  Extracurriculars: {', '.join(sorted(categories))}")

    # Sports
    sports = school.get("sports", [])
    if isinstance(sports, list) and sports:
        sport_names = [s.get("sport", "") for s in sports if isinstance(s, dict)]
        if sport_names:
            parts.append(f"  Sports: {', '.join(sport_names[:5])}")

    return "\n".join(parts)


@tool
def search_schools_tool(
    level: Optional[str] = None,
    budget_max: Optional[float] = None,
    neighborhood: Optional[str] = None,
    school_type: Optional[str] = None,
    religious_orientation: Optional[str] = None,
    has_wheelchair_access: Optional[bool] = None,
    has_special_needs_support: Optional[bool] = None,
    has_scholarships: Optional[bool] = None,
    has_transportation: Optional[bool] = None,
    methodology: Optional[str] = None,
) -> str:
    """Search Manhattan schools by criteria. Returns matching schools with details.

    Args:
        level: School level - one of: 'elementary', 'middle', 'high', 'k12', 'university'.
               Use 'elementary' for K-5, 'middle' for 6-8, 'high' for 9-12.
        budget_max: Maximum annual tuition in USD. Use 0 for only free/public schools.
                    Example: 50000 for schools up to $50K/year.
        neighborhood: Manhattan neighborhood name. Examples: 'Upper East Side',
                      'Upper West Side', 'Midtown', 'Harlem', 'Chelsea', 'Tribeca'.
        school_type: Type of school - one of: 'private', 'public', 'charter', 'parochial'.
        religious_orientation: Religious affiliation - one of: 'secular', 'catholic',
                              'jewish_reform', 'jewish_orthodox', 'episcopal', 'quaker'.
        has_wheelchair_access: Set to true if wheelchair accessibility is required.
        has_special_needs_support: Set to true if special needs programs are needed.
        has_scholarships: Set to true if financial aid or scholarships are needed.
        has_transportation: Set to true if school transportation is needed.
        methodology: Teaching approach - one of: 'traditional', 'progressive',
                     'montessori', 'waldorf', 'IB', 'stem_focus', 'inquiry_based'.
    """
    try:
        results = search_schools(
            level=level,
            budget_max=budget_max,
            neighborhood=neighborhood,
            school_type=school_type,
            religious_orientation=religious_orientation,
            has_wheelchair_access=has_wheelchair_access,
            has_special_needs_support=has_special_needs_support,
            has_scholarships=has_scholarships,
            has_transportation=has_transportation,
            methodology=methodology,
            limit=10,
        )

        if not results:
            return "No schools found matching those criteria. Try broadening your search — for example, remove the neighborhood filter or increase the budget."

        output = f"Found {len(results)} matching schools:\n\n"
        for i, school in enumerate(results, 1):
            output += f"{i}. {_format_school_summary(school)}\n\n"

        return output

    except Exception as e:
        logger.exception(f"search_schools_tool error: {e}")
        return f"Error searching schools: {str(e)}"


@tool
def get_school_details(school_slug: str) -> str:
    """Get comprehensive details about a specific school by its slug name.

    Use this when a parent asks about a specific school, wants to compare
    features, or needs detailed information about programs, accessibility,
    or admissions.

    Args:
        school_slug: The URL-friendly name of the school. Examples:
                     'trinity-school', 'ps-6', 'ideal-school',
                     'stuyvesant-high-school', 'success-academy-harlem'.
                     Use lowercase with hyphens.
    """
    try:
        school = get_school_by_slug(school_slug)

        if not school:
            return f"School '{school_slug}' not found. Available school slugs can be found by using search_schools_tool first."

        output = _format_school_summary(school) + "\n\n"

        # Additional details
        output += "--- DETAILED INFO ---\n"

        if school.get("phone"):
            output += f"Phone: {school['phone']}\n"
        if school.get("website"):
            output += f"Website: {school['website']}\n"
        if school.get("description"):
            output += f"Description: {school['description']}\n"
        if school.get("founded_year"):
            output += f"Founded: {school['founded_year']}\n"
        if school.get("total_enrollment"):
            output += f"Total enrollment: {school['total_enrollment']} students\n"
        if school.get("student_teacher_ratio"):
            output += f"Student-teacher ratio: {school['student_teacher_ratio']}\n"

        # Tuition details
        tuition_min = school.get("annual_tuition_min", 0) or 0
        tuition_max = school.get("annual_tuition_max", 0) or 0
        if tuition_max > 0:
            output += f"Tuition range: ${tuition_min:,.0f} - ${tuition_max:,.0f}/year\n"
        else:
            output += "Tuition: Free\n"

        # Special needs detail
        sn = school.get("special_needs_programs", [])
        if isinstance(sn, list) and sn:
            output += "\nSpecial Needs Programs:\n"
            for prog in sn:
                if isinstance(prog, dict):
                    output += f"  - {prog.get('condition', 'N/A')}: {prog.get('details', 'N/A')}\n"

        # Teacher certifications
        certs = school.get("teacher_certifications", [])
        if isinstance(certs, list) and certs:
            output += "\nTeacher Certifications:\n"
            for cert in certs:
                if isinstance(cert, dict):
                    pct = cert.get("pct", "")
                    pct_str = f" ({pct}%)" if pct else ""
                    output += f"  - {cert.get('cert', 'N/A')}{pct_str}\n"

        # Extracurriculars detail
        extras = school.get("extracurriculars", [])
        if isinstance(extras, list) and extras:
            output += "\nExtracurricular Activities:\n"
            for e in extras:
                if isinstance(e, dict):
                    cost = e.get("cost", 0) or 0
                    cost_str = f" (${cost:,.0f} extra)" if cost > 0 else " (included)"
                    desc = e.get("description", "")
                    desc_str = f" — {desc}" if desc else ""
                    output += f"  - {e.get('name', 'N/A')} [{e.get('category', '')}]{cost_str}{desc_str}\n"

        # Sports detail
        sports = school.get("sports", [])
        if isinstance(sports, list) and sports:
            output += "\nSports Programs:\n"
            for s in sports:
                if isinstance(s, dict):
                    tourn = " (competes in tournaments)" if s.get("tournaments") else ""
                    details = f" — {s.get('details', '')}" if s.get("details") else ""
                    output += f"  - {s.get('sport', 'N/A')}{tourn}{details}\n"

        return output

    except Exception as e:
        logger.exception(f"get_school_details error: {e}")
        return f"Error retrieving school details: {str(e)}"


# Export all tools for the orchestrator
school_finder_tools = [search_schools_tool, get_school_details]
