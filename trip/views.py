"""
Trip Views (Controllers) — like controllers/tripController.js in Express

POST /api/trip/plan
  1. Validate inputs
  2. Geocode all 3 locations
  3. Get driving route (2 legs)
  4. Run HOS engine
  5. Return full JSON response
"""
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .route_service import geocode, get_full_route
from .hos_engine import calculate_trip

logger = logging.getLogger('trip.views')


class PlanTripView(APIView):
    """
    POST /api/trip/plan
    Takes trip details, calculates route + HOS schedule, returns everything.
    """

    def post(self, request):
        logger.info("=" * 50)
        logger.info("TRIP PLAN REQUEST RECEIVED")
        logger.info("=" * 50)

        data = request.data

        current_location = data.get('current_location', '').strip()
        pickup_location = data.get('pickup_location', '').strip()
        dropoff_location = data.get('dropoff_location', '').strip()
        current_cycle_hours = data.get('current_cycle_hours', 0)

        # Validate inputs
        if not all([current_location, pickup_location, dropoff_location]):
            logger.warning("Missing required fields!")
            return Response(
                {"error": "All location fields are required (current_location, pickup_location, dropoff_location)"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            current_cycle_hours = float(current_cycle_hours)
        except (TypeError, ValueError):
            return Response(
                {"error": "current_cycle_hours must be a number"},
                status=status.HTTP_400_BAD_REQUEST
            )

        if current_cycle_hours < 0 or current_cycle_hours > 70:
            return Response(
                {"error": "current_cycle_hours must be between 0 and 70"},
                status=status.HTTP_400_BAD_REQUEST
            )

        logger.info(f"From: {current_location} | Pickup: {pickup_location} | Dropoff: {dropoff_location}")
        logger.info(f"Cycle hours: {current_cycle_hours}")

        # Step 1: Geocode all 3 locations
        try:
            logger.info("Step 1: Geocoding locations...")
            current_geo = geocode(current_location)
            pickup_geo = geocode(pickup_location)
            dropoff_geo = geocode(dropoff_location)
        except ValueError as e:
            logger.error(f"Geocoding failed: {e}")
            return Response(
                {"error": f"Geocoding failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Geocoding error: {e}")
            return Response(
                {"error": "Failed to geocode locations. Please check the location names and try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 2: Get driving route
        try:
            logger.info("Step 2: Getting route...")
            route = get_full_route(current_geo, pickup_geo, dropoff_geo)
        except ValueError as e:
            logger.error(f"Routing failed: {e}")
            return Response(
                {"error": f"Routing failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return Response(
                {"error": "Failed to calculate route. Please try again."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 3: Run HOS engine
        try:
            logger.info("Step 3: Running HOS engine...")
            locations = {
                "current": {"lat": current_geo["lat"], "lng": current_geo["lng"], "name": current_location},
                "pickup":  {"lat": pickup_geo["lat"],  "lng": pickup_geo["lng"],  "name": pickup_location},
                "dropoff": {"lat": dropoff_geo["lat"], "lng": dropoff_geo["lng"], "name": dropoff_location},
            }
            trip_result = calculate_trip(route["legs"], current_cycle_hours, locations)
        except Exception as e:
            logger.error(f"HOS engine error: {e}")
            return Response(
                {"error": f"HOS calculation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Step 4: Build and return response
        response_data = {
            "total_miles": trip_result["total_miles"],
            "total_driving_hours": trip_result["total_driving_hours"],
            "total_days": trip_result["total_days"],
            "route_geometry": route["geometry"],
            "stops": trip_result["stops"],
            "daily_logs": trip_result["daily_logs"],
            "cycle_summary": trip_result["cycle_summary"],
        }

        logger.info(f"Step 4: Returning response ({trip_result['total_days']} days, {trip_result['total_miles']} miles)")
        logger.info("=" * 50)

        return Response(response_data)
