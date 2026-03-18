"""
EduScout Maps Tool (Day 9 — Google Routes API + Geocoding)
Calculates commute times between addresses and schools.

Uses:
- Google Routes API (v2) for travel time/distance (replaces legacy Distance Matrix)
- Google Geocoding API for address → coordinates

Env vars required:
    GOOGLE_MAPS_API_KEY
"""

import os
import logging
import requests
from typing import Optional

logger = logging.getLogger("eduscout.maps")

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"
GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"


def geocode_address(address: str) -> Optional[dict]:
    """
    Convert a text address to lat/lng coordinates.

    Returns:
        {"lat": float, "lng": float, "formatted_address": str} or None on failure.
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.error("GOOGLE_MAPS_API_KEY not set")
        return None

    try:
        resp = requests.get(
            GEOCODE_URL,
            params={"address": address, "key": GOOGLE_MAPS_API_KEY},
            timeout=10,
        )
        data = resp.json()

        if data.get("status") != "OK" or not data.get("results"):
            logger.warning(f"Geocoding failed for '{address}': {data.get('status')}")
            return None

        result = data["results"][0]
        location = result["geometry"]["location"]

        return {
            "lat": location["lat"],
            "lng": location["lng"],
            "formatted_address": result.get("formatted_address", address),
        }

    except Exception as e:
        logger.exception(f"Geocoding error for '{address}': {e}")
        return None


def calculate_route(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    travel_mode: str = "TRANSIT",
) -> Optional[dict]:
    """
    Calculate route between two coordinates using Google Routes API v2.

    Args:
        travel_mode: "TRANSIT", "DRIVE", "WALK", "BICYCLE"

    Returns:
        {"distance_meters": int, "duration_seconds": int, "duration_text": str, "distance_text": str, "mode": str}
        or None on failure.
    """
    if not GOOGLE_MAPS_API_KEY:
        logger.error("GOOGLE_MAPS_API_KEY not set")
        return None

    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": "routes.duration,routes.distanceMeters,routes.legs.duration,routes.legs.distanceMeters",
    }

    body = {
        "origin": {
            "location": {
                "latLng": {"latitude": origin_lat, "longitude": origin_lng}
            }
        },
        "destination": {
            "location": {
                "latLng": {"latitude": dest_lat, "longitude": dest_lng}
            }
        },
        "travelMode": travel_mode,
    }

    try:
        resp = requests.post(ROUTES_URL, json=body, headers=headers, timeout=15)
        data = resp.json()

        if "routes" not in data or not data["routes"]:
            logger.warning(f"No routes found: {data}")
            return None

        route = data["routes"][0]
        distance_m = route.get("distanceMeters", 0)
        duration_raw = route.get("duration", "0s")

        # duration comes as "1534s" string — parse to int seconds
        duration_seconds = int(duration_raw.replace("s", ""))

        return {
            "distance_meters": distance_m,
            "duration_seconds": duration_seconds,
            "duration_text": _format_duration(duration_seconds),
            "distance_text": _format_distance(distance_m),
            "mode": travel_mode,
        }

    except Exception as e:
        logger.exception(f"Routes API error: {e}")
        return None


def calculate_commute(
    address: str,
    school_lat: float,
    school_lng: float,
    school_name: str,
    modes: list[str] = None,
) -> dict:
    """
    High-level: geocode address and calculate commute to a school for multiple modes.

    Returns:
        {
            "origin_address": str,
            "school_name": str,
            "routes": [{"mode": str, "duration_text": str, "distance_text": str, ...}, ...],
            "summary": str  # formatted for WhatsApp
        }
    """
    if modes is None:
        modes = ["TRANSIT", "DRIVE"]

    geo = geocode_address(address)
    if not geo:
        return {
            "origin_address": address,
            "school_name": school_name,
            "routes": [],
            "error": f"Could not find the address: '{address}'. Please provide a more specific address.",
        }

    routes = []
    for mode in modes:
        result = calculate_route(geo["lat"], geo["lng"], school_lat, school_lng, mode)
        if result:
            routes.append(result)

    # Build formatted summary
    mode_emoji = {"TRANSIT": "🚇", "DRIVE": "🚗", "WALK": "🚶", "BICYCLE": "🚲"}

    summary_lines = [f"📍 Commute to {school_name}"]
    summary_lines.append(f"From: {geo['formatted_address']}\n")

    if routes:
        for r in routes:
            emoji = mode_emoji.get(r["mode"], "🗺️")
            summary_lines.append(f"{emoji} {r['mode'].title()}: {r['duration_text']} ({r['distance_text']})")
    else:
        summary_lines.append("⚠️ Could not calculate routes. Please try again.")

    return {
        "origin_address": geo["formatted_address"],
        "origin_lat": geo["lat"],
        "origin_lng": geo["lng"],
        "school_name": school_name,
        "routes": routes,
        "summary": "\n".join(summary_lines),
    }


def _format_duration(seconds: int) -> str:
    """Convert seconds to human-readable duration."""
    if seconds < 60:
        return f"{seconds} sec"
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    remaining = minutes % 60
    if remaining == 0:
        return f"{hours} hr"
    return f"{hours} hr {remaining} min"


def _format_distance(meters: int) -> str:
    """Convert meters to human-readable distance."""
    if meters < 1000:
        return f"{meters} m"
    km = meters / 1000
    return f"{km:.1f} km"
