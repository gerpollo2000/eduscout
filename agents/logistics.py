"""
EduScout Logistics Agent (Day 9)
LangChain tools for calculating commute times and managing parent addresses.

Tools:
- calculate_commute_to_school: Commute from any address to a school
- save_parent_address: Save home/work address for future commute lookups
"""

import logging
from typing import Optional
from decimal import Decimal

from langchain_core.tools import tool

from tools.database import query, execute, get_school_by_slug
from tools.maps import geocode_address, calculate_commute

logger = logging.getLogger("eduscout.logistics")


def _find_school(school_name: str) -> Optional[dict]:
    """
    Find a school by name (fuzzy match) or slug.
    Returns the school dict or None.
    """
    # Try exact slug first
    school = get_school_by_slug(school_name.lower().replace(" ", "-"))
    if school:
        return school

    # Fuzzy name search
    results = query(
        "SELECT id, name, slug, address, latitude, longitude FROM schools WHERE LOWER(name) LIKE LOWER(%s) LIMIT 3",
        (f"%{school_name}%",),
    )

    if results:
        return results[0]

    return None


def _get_parent_address(parent_id: int, address_type: str = "home") -> Optional[dict]:
    """Get saved parent address from DB."""
    prefix = "home" if address_type == "home" else "work"
    results = query(
        f"SELECT {prefix}_address, {prefix}_latitude, {prefix}_longitude FROM parents WHERE id = %s",
        (parent_id,),
    )
    if results:
        row = results[0]
        addr = row.get(f"{prefix}_address")
        lat = row.get(f"{prefix}_latitude")
        lng = row.get(f"{prefix}_longitude")
        if addr and lat and lng:
            return {"address": addr, "lat": float(lat), "lng": float(lng)}
    return None


@tool
def calculate_commute_to_school(
    school_name: str,
    address: str = "",
    parent_id: int = 0,
    address_type: str = "",
) -> str:
    """Calculate commute time from an address to a school (transit + driving).

    Use this when a parent asks about travel time, distance, or commute to a school.

    Args:
        school_name: Name of the school (e.g., "Trinity School", "Stuyvesant").
        address: Street address to commute from (e.g., "350 5th Ave, New York").
                 If empty, will try to use the parent's saved home/work address.
        parent_id: The parent's ID (to look up saved addresses). Comes from session context.
        address_type: "home" or "work" — which saved address to use if no address given.
                      If empty and no address given, defaults to "home".
    """
    # 1. Find the school
    school = _find_school(school_name)
    if not school:
        return f"I couldn't find a school matching '{school_name}' in our database. Could you check the name?"

    school_lat = school.get("latitude")
    school_lng = school.get("longitude")

    if not school_lat or not school_lng:
        return f"I have {school['name']} in our database but don't have its exact coordinates. I can't calculate the commute yet."

    school_lat = float(school_lat)
    school_lng = float(school_lng)

    # 2. Resolve origin address
    origin_address = address.strip()

    if not origin_address and parent_id:
        # Try saved address
        addr_type = address_type if address_type in ("home", "work") else "home"
        saved = _get_parent_address(parent_id, addr_type)
        if saved:
            origin_address = saved["address"]
            logger.info(f"Using saved {addr_type} address: {origin_address}")
        else:
            # Try the other type
            other = "work" if addr_type == "home" else "home"
            saved = _get_parent_address(parent_id, other)
            if saved:
                origin_address = saved["address"]
                logger.info(f"Using saved {other} address (fallback): {origin_address}")

    if not origin_address:
        return (
            f"I'd love to calculate the commute to {school['name']}! "
            "Could you share your address? For example: '350 5th Ave, New York' "
            "or tell me to save your home/work address for future calculations."
        )

    # 3. Calculate commute
    result = calculate_commute(
        address=origin_address,
        school_lat=school_lat,
        school_lng=school_lng,
        school_name=school["name"],
    )

    if result.get("error"):
        return result["error"]

    return result.get("summary", "Could not calculate commute. Please try again.")


@tool
def save_parent_address(
    address: str,
    address_type: str,
    parent_id: int,
) -> str:
    """Save a parent's home or work address for future commute calculations.

    Use this when a parent shares their home or work address, or says things like:
    - "I live at 200 E 82nd St"
    - "My office is at 350 5th Ave"
    - "Save my home address..."

    Args:
        address: The street address to save (e.g., "200 E 82nd St, New York, NY").
        address_type: "home" or "work".
        parent_id: The parent's ID from session context.
    """
    if address_type not in ("home", "work"):
        return "Please specify whether this is your 'home' or 'work' address."

    if not address.strip():
        return "I need an address to save. Could you share it?"

    if not parent_id:
        return "I couldn't identify your account. Please try again."

    # Geocode to get coordinates
    geo = geocode_address(address.strip())
    if not geo:
        return f"I couldn't verify the address '{address}'. Could you double-check it? Include the city and state for best results."

    # Save to DB
    prefix = "home" if address_type == "home" else "work"
    try:
        execute(
            f"UPDATE parents SET {prefix}_address = %s, {prefix}_latitude = %s, {prefix}_longitude = %s, updated_at = NOW() WHERE id = %s",
            (geo["formatted_address"], geo["lat"], geo["lng"], parent_id),
        )

        return (
            f"✅ Saved your {address_type} address: {geo['formatted_address']}\n\n"
            f"I'll use this for future commute calculations. "
            f"You can ask me things like 'How far is Trinity School from {address_type}?'"
        )

    except Exception as e:
        logger.exception(f"Failed to save address: {e}")
        return "I had trouble saving your address. Please try again."


# Export
logistics_tools = [calculate_commute_to_school, save_parent_address]
