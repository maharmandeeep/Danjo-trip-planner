"""
HOS Engine — Core algorithm that simulates a truck driver's trip.

Takes route data + cycle hours, applies all FMCSA HOS rules, and returns:
  - daily_logs[]   — segments for each day (for log sheet grid)
  - stops[]        — map markers (start, pickup, fuel, rest, dropoff)
  - cycle_summary  — 70-hour cycle tracking

HOS Rules implemented:
  1. 70-Hour/8-Day Cycle     — max 70 on-duty hours in rolling 8 days
  2. 14-Hour Window          — can't drive after 14hrs from shift start
  3. 11-Hour Driving Limit   — max 11hrs driving per shift
  4. 30-Min Break            — required after 8hrs cumulative driving
  5. 10-Hour Off-Duty        — between shifts (resets 11hr + 14hr)
  6. Fuel every 1,000 miles  — 30-min fuel stop (on-duty not driving)
"""
import logging
from datetime import date, timedelta

logger = logging.getLogger('trip.hos_engine')

# Constants
MAX_DRIVING_PER_SHIFT = 11.0    # hours
MAX_DUTY_WINDOW = 14.0          # hours
DRIVING_BEFORE_BREAK = 8.0      # hours
BREAK_DURATION = 0.5            # 30 minutes
REST_DURATION = 10.0            # hours
MAX_CYCLE_HOURS = 70.0          # hours
CYCLE_RESTART_DURATION = 34.0   # hours
FUEL_INTERVAL_MILES = 1000      # miles
FUEL_STOP_DURATION = 0.5        # 30 minutes
PICKUP_DROPOFF_DURATION = 1.0   # hours
PRETIP_INSPECTION_DURATION = 0.5  # 30 minutes
SHIFT_START_HOUR = 6.0          # 6:00 AM
AVG_SPEED_MPH = 65              # for mile/time calculations


def calculate_trip(route_legs, current_cycle_hours, locations, start_date=None):
    """
    Main entry point. Simulates the full trip with HOS rules.

    Args:
        route_legs: list of dicts, each with:
            - distance_miles: float
            - duration_hours: float
        current_cycle_hours: float (hours already used in 70hr cycle)
        locations: dict with keys:
            - current: {"lat", "lng", "name"}
            - pickup:  {"lat", "lng", "name"}
            - dropoff: {"lat", "lng", "name"}
        start_date: date object (defaults to today)

    Returns: {
        "total_miles": float,
        "total_driving_hours": float,
        "total_days": int,
        "stops": [...],
        "daily_logs": [...],
        "cycle_summary": {...}
    }
    """
    if start_date is None:
        start_date = date.today()

    logger.info("=" * 50)
    logger.info("HOS ENGINE START")
    logger.info("=" * 50)

    total_route_miles = sum(leg["distance_miles"] for leg in route_legs)
    total_route_hours = sum(leg["duration_hours"] for leg in route_legs)
    logger.info(f"Total route: {total_route_miles} miles, {total_route_hours} hours driving")
    logger.info(f"Cycle hours used: {current_cycle_hours}/70")

    # Initialize state
    state = {
        "current_time": 0.0,           # hours since midnight of current day
        "current_day": 1,
        "shift_driving": 0.0,          # driving hours in current shift (max 11)
        "shift_duty": 0.0,             # total duty hours since shift start (max 14)
        "driving_since_break": 0.0,    # driving since last 30-min break (max 8)
        "cycle_hours": float(current_cycle_hours),
        "miles_since_fuel": 0.0,
        "total_miles_driven": 0.0,
        "total_driving_hours": 0.0,
        "segments": [],                # current day's segments
        "daily_logs": [],              # completed days
        "stops": [],                   # map markers
        "start_date": start_date,
        "shift_started": False,        # has the shift started today?
    }

    # Fill off-duty from midnight to shift start
    if SHIFT_START_HOUR > 0:
        _add_segment(state, "off_duty", SHIFT_START_HOUR, "Off Duty")
    state["current_time"] = SHIFT_START_HOUR

    # Add start stop
    state["stops"].append({
        "type": "start",
        "location": locations["current"]["name"],
        "lat": locations["current"]["lat"],
        "lng": locations["current"]["lng"],
        "time": _format_time(SHIFT_START_HOUR),
        "day": 1,
    })

    # Pre-trip inspection
    _start_shift(state)
    _add_on_duty(state, PRETIP_INSPECTION_DURATION,
                 f"Pre-trip inspection, {locations['current']['name']}")

    # Process each leg
    leg_types = ["pickup", "dropoff"]
    for i, leg in enumerate(route_legs):
        leg_type = leg_types[i]
        loc = locations[leg_type]

        logger.info(f"--- Leg {i+1}: driving to {loc['name']} ({leg['distance_miles']} mi, {leg['duration_hours']} hrs) ---")

        _drive_leg(state, leg["distance_miles"], leg["duration_hours"], loc["name"])

        # Arrived — add pickup/dropoff stop and on-duty time
        stop_type = leg_type
        state["stops"].append({
            "type": stop_type,
            "location": loc["name"],
            "lat": loc["lat"],
            "lng": loc["lng"],
            "time": _format_time(state["current_time"]),
            "day": state["current_day"],
            "duration_hrs": PICKUP_DROPOFF_DURATION,
        })

        logger.info(f"Arrived at {loc['name']} — {stop_type} ({PICKUP_DROPOFF_DURATION} hr)")

        # Check if we need rest before the on-duty pickup/dropoff
        _ensure_can_work(state, PICKUP_DROPOFF_DURATION)
        _add_on_duty(state, PICKUP_DROPOFF_DURATION, f"{stop_type.title()}, {loc['name']}")

    # Trip complete — fill rest of last day as off-duty
    remaining = 24.0 - state["current_time"]
    if remaining > 0:
        _add_segment(state, "off_duty", remaining, "Off Duty — Trip Complete")

    # Save the last day
    _save_day(state)

    total_days = len(state["daily_logs"])
    logger.info("=" * 50)
    logger.info(f"HOS ENGINE DONE: {total_days} days, {state['total_miles_driven']} miles")
    logger.info("=" * 50)

    # Calculate cycle summary
    on_duty_this_trip = round(state["cycle_hours"] - current_cycle_hours, 1)
    cycle_after = round(state["cycle_hours"], 1)

    return {
        "total_miles": round(state["total_miles_driven"], 1),
        "total_driving_hours": round(state["total_driving_hours"], 1),
        "total_days": total_days,
        "stops": state["stops"],
        "daily_logs": state["daily_logs"],
        "cycle_summary": {
            "cycle_before": current_cycle_hours,
            "on_duty_this_trip": on_duty_this_trip,
            "cycle_after": cycle_after,
            "remaining": round(MAX_CYCLE_HOURS - cycle_after, 1),
            "limit": MAX_CYCLE_HOURS,
        },
    }


def _drive_leg(state, leg_miles, leg_hours, destination):
    """Drive a single leg, inserting breaks/rests/fuel as needed."""
    remaining_miles = leg_miles
    remaining_hours = leg_hours

    while remaining_hours > 0.01:  # small epsilon to avoid float issues
        # How long can we drive before hitting any limit?
        max_by_driving = MAX_DRIVING_PER_SHIFT - state["shift_driving"]
        max_by_window = MAX_DUTY_WINDOW - state["shift_duty"]
        max_by_break = DRIVING_BEFORE_BREAK - state["driving_since_break"]
        max_by_cycle = MAX_CYCLE_HOURS - state["cycle_hours"]

        # Fuel: how many hours until 1000-mile mark
        if state["miles_since_fuel"] < FUEL_INTERVAL_MILES:
            miles_to_fuel = FUEL_INTERVAL_MILES - state["miles_since_fuel"]
            max_by_fuel = miles_to_fuel / AVG_SPEED_MPH if AVG_SPEED_MPH > 0 else 999
        else:
            max_by_fuel = 0  # need fuel now

        max_drive = min(max_by_driving, max_by_window, max_by_break,
                        max_by_cycle, max_by_fuel, remaining_hours)

        # Check if we need a midnight crossover before we can drive max_drive
        time_until_midnight = 24.0 - state["current_time"]
        if max_drive > time_until_midnight and time_until_midnight > 0:
            max_drive = time_until_midnight

        if max_drive <= 0.01:
            # Can't drive — figure out why and take appropriate action
            if max_by_cycle <= 0.01:
                logger.info(f"  CYCLE LIMIT HIT — 34-hour restart needed")
                _take_34hr_restart(state)
            elif max_by_driving <= 0.01 or max_by_window <= 0.01:
                logger.info(f"  SHIFT LIMIT HIT — 10-hour rest needed (driving={state['shift_driving']}/11, window={state['shift_duty']}/14)")
                _take_10hr_rest(state, destination)
            elif max_by_break <= 0.01:
                logger.info(f"  8-HR DRIVING — 30-min break needed")
                _take_30min_break(state)
            elif max_by_fuel <= 0.01:
                logger.info(f"  FUEL STOP — {state['miles_since_fuel']} miles since last fuel")
                _take_fuel_stop(state, destination)
            elif time_until_midnight <= 0.01:
                # Midnight crossover — save day, start new one
                _save_day(state)
                _start_new_day(state)
            continue

        # Drive for max_drive hours
        drive_miles = remaining_miles * (max_drive / remaining_hours) if remaining_hours > 0 else 0
        drive_miles = round(drive_miles, 1)

        _add_segment(state, "driving", max_drive, f"Driving to {destination}")

        state["shift_driving"] += max_drive
        state["shift_duty"] += max_drive
        state["driving_since_break"] += max_drive
        state["cycle_hours"] += max_drive
        state["total_driving_hours"] += max_drive
        state["miles_since_fuel"] += drive_miles
        state["total_miles_driven"] += drive_miles

        remaining_hours -= max_drive
        remaining_miles -= drive_miles

        logger.info(f"  Drive {round(max_drive, 1)}hrs ({round(drive_miles, 1)}mi) | "
                     f"shift_driving={round(state['shift_driving'], 1)}/11 | "
                     f"window={round(state['shift_duty'], 1)}/14 | "
                     f"since_break={round(state['driving_since_break'], 1)}/8")

        # Check if fuel is needed after this drive segment
        if state["miles_since_fuel"] >= FUEL_INTERVAL_MILES - 0.1 and remaining_hours > 0.01:
            logger.info(f"  FUEL STOP — {round(state['miles_since_fuel'], 1)} miles since last fuel")
            _take_fuel_stop(state, destination)


def _ensure_can_work(state, duration):
    """Ensure the driver can do on-duty work for the given duration."""
    available_window = MAX_DUTY_WINDOW - state["shift_duty"]
    available_cycle = MAX_CYCLE_HOURS - state["cycle_hours"]

    if available_cycle < duration:
        _take_34hr_restart(state)
    elif available_window < duration:
        _take_10hr_rest(state, "")


def _start_shift(state):
    """Mark the shift as started."""
    state["shift_started"] = True


def _add_on_duty(state, duration, note):
    """Add on-duty (not driving) time."""
    # Handle midnight crossover
    while duration > 0.01:
        time_until_midnight = 24.0 - state["current_time"]
        chunk = min(duration, time_until_midnight)

        if chunk <= 0.01:
            _save_day(state)
            _start_new_day(state)
            continue

        _add_segment(state, "on_duty", chunk, note)
        state["shift_duty"] += chunk
        state["cycle_hours"] += chunk
        duration -= chunk

        if state["current_time"] >= 24.0 - 0.01 and duration > 0.01:
            _save_day(state)
            _start_new_day(state)


def _take_30min_break(state):
    """Take a 30-minute break (off-duty). Resets driving_since_break."""
    remaining = BREAK_DURATION
    while remaining > 0.01:
        time_until_midnight = 24.0 - state["current_time"]
        chunk = min(remaining, time_until_midnight)

        if chunk <= 0.01:
            _save_day(state)
            _start_new_day(state)
            continue

        _add_segment(state, "off_duty", chunk, "30-min break")
        remaining -= chunk

        if state["current_time"] >= 24.0 - 0.01 and remaining > 0.01:
            _save_day(state)
            _start_new_day(state)

    state["driving_since_break"] = 0.0
    # Break counts toward the 14hr window but NOT toward cycle hours
    state["shift_duty"] += BREAK_DURATION


def _take_fuel_stop(state, near_location):
    """Take a 30-minute fuel stop (on-duty not driving)."""
    note = f"Fuel stop"
    if near_location:
        note = f"Fuel stop near {near_location}"

    state["stops"].append({
        "type": "fuel",
        "location": near_location or "En route",
        "lat": 0, "lng": 0,  # Will be interpolated if we have geometry
        "time": _format_time(state["current_time"]),
        "day": state["current_day"],
        "duration_hrs": FUEL_STOP_DURATION,
    })

    _add_on_duty(state, FUEL_STOP_DURATION, note)
    state["miles_since_fuel"] = 0.0
    logger.info(f"  Fuel stop complete. Miles reset.")


def _take_10hr_rest(state, near_location):
    """Take 10-hour rest (sleeper berth). Resets shift counters."""
    logger.info(f"  REST: 10-hour sleeper berth")

    if near_location:
        state["stops"].append({
            "type": "rest",
            "location": near_location or "En route",
            "lat": 0, "lng": 0,
            "time": _format_time(state["current_time"]),
            "day": state["current_day"],
            "duration_hrs": REST_DURATION,
        })

    remaining = REST_DURATION
    while remaining > 0.01:
        time_until_midnight = 24.0 - state["current_time"]
        chunk = min(remaining, time_until_midnight)

        if chunk <= 0.01:
            _save_day(state)
            _start_new_day(state)
            continue

        _add_segment(state, "sleeper", chunk,
                     f"Sleeper Berth" + (f", {near_location}" if near_location else ""))
        remaining -= chunk

        if state["current_time"] >= 24.0 - 0.01 and remaining > 0.01:
            _save_day(state)
            _start_new_day(state)

    # Reset shift counters after 10hr rest
    state["shift_driving"] = 0.0
    state["shift_duty"] = 0.0
    state["driving_since_break"] = 0.0

    # Pre-trip inspection for new shift
    _add_on_duty(state, PRETIP_INSPECTION_DURATION,
                 f"Pre-trip inspection")


def _take_34hr_restart(state):
    """Take 34-hour restart. Resets cycle to 0."""
    logger.info(f"  34-HOUR RESTART — cycle reset")

    state["stops"].append({
        "type": "rest",
        "location": "En route (34hr restart)",
        "lat": 0, "lng": 0,
        "time": _format_time(state["current_time"]),
        "day": state["current_day"],
        "duration_hrs": CYCLE_RESTART_DURATION,
    })

    remaining = CYCLE_RESTART_DURATION
    while remaining > 0.01:
        time_until_midnight = 24.0 - state["current_time"]
        chunk = min(remaining, time_until_midnight)

        if chunk <= 0.01:
            _save_day(state)
            _start_new_day(state)
            continue

        _add_segment(state, "sleeper", chunk, "34-hour restart")
        remaining -= chunk

        if state["current_time"] >= 24.0 - 0.01 and remaining > 0.01:
            _save_day(state)
            _start_new_day(state)

    # Reset everything
    state["shift_driving"] = 0.0
    state["shift_duty"] = 0.0
    state["driving_since_break"] = 0.0
    state["cycle_hours"] = 0.0

    # Pre-trip inspection for new shift
    _add_on_duty(state, PRETIP_INSPECTION_DURATION, "Pre-trip inspection")


def _add_segment(state, status, duration, note=""):
    """Add a segment to the current day's log."""
    start = round(state["current_time"], 2)
    end = round(start + duration, 2)

    # Clamp to 24.0 max for this day
    if end > 24.0:
        end = 24.0
        duration = end - start

    state["segments"].append({
        "status": status,
        "start": round(start, 2),
        "end": round(end, 2),
        "note": note,
    })
    state["current_time"] = end


def _save_day(state):
    """Save current day's segments to daily_logs."""
    day_num = state["current_day"]
    day_date = state["start_date"] + timedelta(days=day_num - 1)

    # Calculate hours summary
    hours = {"off_duty": 0, "sleeper": 0, "driving": 0, "on_duty": 0}
    total_day_miles = 0

    for seg in state["segments"]:
        dur = round(seg["end"] - seg["start"], 2)
        hours[seg["status"]] += dur
        if seg["status"] == "driving":
            total_day_miles += dur * AVG_SPEED_MPH  # approximation

    # Round all hours
    hours = {k: round(v, 1) for k, v in hours.items()}

    logger.info(f"  === Day {day_num} saved: driving={hours['driving']}h, on_duty={hours['on_duty']}h, "
                f"off_duty={hours['off_duty']}h, sleeper={hours['sleeper']}h ===")

    state["daily_logs"].append({
        "day": day_num,
        "date": day_date.isoformat(),
        "total_miles": round(total_day_miles, 1),
        "segments": state["segments"],
        "hours_summary": hours,
    })


def _start_new_day(state):
    """Start a new day with fresh segments."""
    state["current_day"] += 1
    state["current_time"] = 0.0
    state["segments"] = []
    logger.info(f"--- Day {state['current_day']} ---")


def _format_time(hours_since_midnight):
    """Convert 13.5 -> '1:30 PM'."""
    h = int(hours_since_midnight) % 24
    m = int((hours_since_midnight % 1) * 60)
    period = "AM" if h < 12 else "PM"
    display_h = h % 12
    if display_h == 0:
        display_h = 12
    return f"{display_h}:{m:02d} {period}"
