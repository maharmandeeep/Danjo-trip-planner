"""
Route Service — External API calls for geocoding + routing.

Two functions:
  geocode(location) — "Los Angeles, CA" -> {"lat": 34.05, "lng": -118.24}
  get_route(coords)  — [[lng,lat], [lng,lat]] -> {distance_miles, duration_hours, geometry}
"""
import time
import logging
import requests
from django.conf import settings

logger = logging.getLogger('trip.route_service')

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-hgv"


def geocode(location):
    """
    Convert a place name to lat/lng using Nominatim (OpenStreetMap).
    No API key needed but rate-limited to 1 req/sec.

    Returns: {"lat": float, "lng": float, "display_name": str}
    Raises: ValueError if location not found.
    """
    logger.info(f"Geocoding: {location}")

    resp = requests.get(NOMINATIM_URL, params={
        "q": location,
        "format": "json",
        "limit": 1,
    }, headers={
        "User-Agent": "SpotterELD-TripPlanner/1.0"
    }, timeout=10)
    resp.raise_for_status()

    results = resp.json()
    if not results:
        raise ValueError(f"Could not geocode location: {location}")

    result = results[0]
    lat = float(result["lat"])
    lng = float(result["lon"])
    display_name = result.get("display_name", location)

    logger.info(f"Geocode result: lat={lat}, lng={lng} ({display_name})")

    # Respect Nominatim rate limit
    time.sleep(1.1)

    return {"lat": lat, "lng": lng, "display_name": display_name}


def get_route(start_coord, end_coord):
    """
    Get driving route between two points using OpenRouteService (HGV profile).

    Args:
        start_coord: {"lat": float, "lng": float}
        end_coord:   {"lat": float, "lng": float}

    Returns: {
        "distance_miles": float,
        "duration_hours": float,
        "geometry": [[lat, lng], ...]   # for map polyline
    }
    Raises: ValueError if route cannot be calculated.
    """
    api_key = settings.ORS_API_KEY
    if not api_key:
        raise ValueError("ORS_API_KEY is not set in .env")

    logger.info(f"Getting route: ({start_coord['lat']},{start_coord['lng']}) -> ({end_coord['lat']},{end_coord['lng']})")

    # ORS expects start/end as lng,lat (not lat,lng)
    resp = requests.get(ORS_DIRECTIONS_URL, params={
        "api_key": api_key,
        "start": f"{start_coord['lng']},{start_coord['lat']}",
        "end": f"{end_coord['lng']},{end_coord['lat']}",
    }, timeout=15)
    resp.raise_for_status()

    data = resp.json()

    if not data.get("features"):
        raise ValueError(f"No route found between the given coordinates")

    feature = data["features"][0]
    summary = feature["properties"]["summary"]

    distance_miles = round(summary["distance"] / 1609.34, 1)  # meters -> miles
    duration_hours = round(summary["duration"] / 3600, 2)      # seconds -> hours

    # Convert geometry from [lng, lat] to [lat, lng] for Leaflet
    raw_coords = feature["geometry"]["coordinates"]
    geometry = [[coord[1], coord[0]] for coord in raw_coords]

    logger.info(f"Route result: {distance_miles} miles, {duration_hours} hours, {len(geometry)} geometry points")

    return {
        "distance_miles": distance_miles,
        "duration_hours": duration_hours,
        "geometry": geometry,
    }


def get_full_route(current_coord, pickup_coord, dropoff_coord):
    """
    Get the full two-leg route: current -> pickup -> dropoff.

    Returns: {
        "legs": [leg1, leg2],           # each leg has distance_miles, duration_hours
        "total_miles": float,
        "total_hours": float,
        "geometry": [[lat, lng], ...],  # combined geometry for map
    }
    """
    logger.info("Getting full route (2 legs)...")

    leg1 = get_route(current_coord, pickup_coord)
    leg2 = get_route(pickup_coord, dropoff_coord)

    total_miles = round(leg1["distance_miles"] + leg2["distance_miles"], 1)
    total_hours = round(leg1["duration_hours"] + leg2["duration_hours"], 2)

    # Combine geometry (skip first point of leg2 to avoid duplicate)
    combined_geometry = leg1["geometry"] + leg2["geometry"][1:]

    logger.info(f"Full route: {total_miles} miles, {total_hours} hours (leg1: {leg1['distance_miles']}mi, leg2: {leg2['distance_miles']}mi)")

    return {
        "legs": [
            {
                "distance_miles": leg1["distance_miles"],
                "duration_hours": leg1["duration_hours"],
                "geometry": leg1["geometry"],
            },
            {
                "distance_miles": leg2["distance_miles"],
                "duration_hours": leg2["duration_hours"],
                "geometry": leg2["geometry"],
            },
        ],
        "total_miles": total_miles,
        "total_hours": total_hours,
        "geometry": combined_geometry,
    }
