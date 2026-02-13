# Django Backend — Complete Guide

> If you know Express, you know 80% of this. This doc maps everything to Express so it clicks.

---

## CURRENT STATUS (read this first if continuing from another chat)

**Last updated:** Feb 13, 2026

### What's DONE:
- [x] B1: Project setup — venv, packages, Django project, trip app, settings, CORS, logging, URLs, .gitignore
- [x] Placeholder view (views.py) — accepts POST, validates inputs, returns echo response with logging
- [x] docs/django-backend-guide.md — this file (full reference)
- [x] docs/implementation-plan.md — full plan with 3 trees (requirements, backend, frontend)

### What's NEXT (in order):
- [ ] **B2: trip/route_service.py** — geocode() + get_route() functions calling Nominatim + OpenRouteService
- [ ] **B3: trip/hos_engine.py** — HOS calculation engine (the core algorithm)
- [ ] **B4: Wire views.py** — connect views.py to call route_service → hos_engine → return full response
- [ ] **B5: Test with curl/Postman** — 5 test cases (see Section 4 below)

### What needs attention:
- `.env` file has `ORS_API_KEY=your_key_here` — needs a REAL key from https://openrouteservice.org/dev/#/signup
- Server not yet tested (start with: `source venv/bin/activate && python manage.py runserver`)

### Files that exist:
```
danjo/
├── config/settings.py    ← CONFIGURED (DRF, CORS, logging, ORS key from .env)
├── config/urls.py        ← CONFIGURED (routes /api/trip/ → trip app)
├── trip/urls.py          ← CREATED (routes /plan → PlanTripView)
├── trip/views.py         ← PLACEHOLDER (echoes inputs back, has logging)
├── trip/route_service.py ← NOT YET CREATED (Step B2)
├── trip/hos_engine.py    ← NOT YET CREATED (Step B3)
├── .env                  ← NEEDS REAL ORS API KEY
├── .gitignore            ← CREATED
├── requirements.txt      ← CREATED (all 5 packages)
└── docs/                 ← CREATED (this guide + implementation plan)
```

---

## BUILD LOG — Step by Step Progress

### Step B1: Project Setup [DONE]
**What we did:**
```bash
# 1. Created virtual environment (like node_modules but for Python)
python3 -m venv venv
# This creates a /venv folder with isolated Python + pip

# 2. Activate it (must do this every time you open terminal)
source venv/bin/activate
# You'll see (venv) in your terminal prompt — means it's active

# 3. Install all packages
pip install django djangorestframework django-cors-headers python-decouple requests
# django            → the web framework (like express)
# djangorestframework → API tools: serializers, Response (like express.json + joi)
# django-cors-headers → allows frontend to call backend (like cors npm)
# python-decouple   → reads .env file (like dotenv npm)
# requests          → makes HTTP calls to external APIs (like axios/node-fetch)

# 4. Create Django project named "config"
django-admin startproject config .
# The "." means create in current directory (not a subfolder)
# This creates: config/settings.py, config/urls.py, manage.py

# 5. Create the "trip" app (our feature module)
python manage.py startapp trip
# This creates: trip/views.py, trip/models.py, trip/urls.py, etc.
# Like creating a routes/trip.js + controllers/trip.js folder

# 6. Save dependencies list
pip freeze > requirements.txt
# Like package.json but manual — records exact versions

# 7. Create .env file with API key
echo "ORS_API_KEY=your_key_here" > .env

# 8. Run migrations (Django housekeeping — even without a DB)
python manage.py migrate

# 9. Start server to verify
python manage.py runserver
# Visit http://localhost:8000 — should see Django welcome page
```

**What we configured in settings.py:**
```python
# Added to INSTALLED_APPS (like require() + app.use() in Express):
INSTALLED_APPS = [
    ...
    'rest_framework',      # DRF — gives us API tools
    'corsheaders',         # CORS — lets frontend talk to us
    'trip',                # Our trip app
]

# Added CORS middleware (like app.use(cors()) in Express):
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',  # Must be near the top!
    ...
]

# Allow all origins for development:
CORS_ALLOW_ALL_ORIGINS = True
```

**What we configured in config/urls.py (root router):**
```python
# Like app.use('/api/trip', tripRoutes) in Express:
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/trip/', include('trip.urls')),  # All /api/trip/* goes to trip app
]
```

**What we created in trip/urls.py (feature router):**
```python
# Like router.post('/plan', planTrip) in Express:
from django.urls import path
from .views import PlanTripView

urlpatterns = [
    path('plan', PlanTripView.as_view(), name='plan-trip'),
]
```

**Files created/modified:**
- `venv/` — virtual environment
- `manage.py` — entry point (auto-generated)
- `config/settings.py` — configured apps, middleware, CORS
- `config/urls.py` — root router
- `trip/` — app folder (auto-generated)
- `trip/urls.py` — feature router (we created this)
- `requirements.txt` — dependency list
- `.env` — API key
- `.gitignore` — ignore venv, .env, __pycache__

---

### Step B2: route_service.py [PENDING]
**What we'll build:** Two functions that call external APIs
- `geocode(location)` — "Los Angeles, CA" -> {lat: 34.05, lng: -118.24}
- `get_route(coords)` — [point_A, point_B] -> {distance, duration, geometry}

**How it works:**
```
TripForm sends "Los Angeles, CA"
  → geocode() calls Nominatim API → gets lat/lng
  → get_route() calls OpenRouteService → gets distance + driving time + map shape
```

**Logging we'll add:**
```python
logger.info(f"Geocoding: {location}")
logger.info(f"Geocode result: lat={lat}, lng={lng}")
logger.info(f"Getting route: {len(coords)} waypoints")
logger.info(f"Route result: {miles} miles, {hours} hours")
```

---

### Step B3: hos_engine.py [PENDING]
**What we'll build:** The brain — simulates the trip applying all HOS rules
- Takes route data + cycle hours
- Returns: daily_logs[], stops[], cycle_summary

**Logging we'll add:**
```python
logger.info(f"=== HOS ENGINE START ===")
logger.info(f"Total route: {total_miles} miles, {total_hours} hours driving")
logger.info(f"Cycle hours used: {cycle_hours}/70")
logger.info(f"--- Day {day} ---")
logger.info(f"  Drive {hours}hrs ({miles}mi) | shift_driving={x}/11 | window={y}/14")
logger.info(f"  BREAK: 30-min rest (8hr driving limit hit)")
logger.info(f"  REST: 10-hour sleeper berth (shift over)")
logger.info(f"  FUEL: 30-min stop ({miles_since_fuel} miles)")
logger.info(f"=== HOS ENGINE DONE: {total_days} days ===")
```

---

### Step B4: views.py — API Endpoint [PENDING]
**What we'll build:** The controller that ties everything together
- Receives POST request with 4 inputs
- Validates inputs
- Calls route_service → calls hos_engine → returns JSON

**Logging we'll add:**
```python
logger.info(f"=== TRIP PLAN REQUEST ===")
logger.info(f"From: {current} | Pickup: {pickup} | Dropoff: {dropoff}")
logger.info(f"Cycle hours: {cycle_hours}")
logger.info(f"Step 1: Geocoding locations...")
logger.info(f"Step 2: Getting route...")
logger.info(f"Step 3: Running HOS engine...")
logger.info(f"Step 4: Returning response ({total_days} days, {total_miles} miles)")
```

---

### Step B5: Testing [PENDING]
**Test with curl/Postman — 5 test cases documented in Section 4 below**

---

## 1. Packages We're Using (and Why)

| Package | What It Does | Express Equivalent |
|---------|-------------|-------------------|
| `django` | The web framework itself. Handles routing, request/response, project structure | `express` |
| `djangorestframework` (DRF) | Adds API-specific tools: serializers (validation), Response objects, browsable API | `express.json()` + `joi` + Swagger combined |
| `django-cors-headers` | Allows frontend (localhost:3000) to call backend (localhost:8000) | `cors` npm package |
| `python-decouple` | Reads `.env` file for secrets (API keys) | `dotenv` npm package |
| `requests` | Makes HTTP calls to external APIs (Nominatim, OpenRouteService) | `axios` or `node-fetch` |

### How packages work in Python vs Node
```
Node/Express way:                    Django way:
─────────────────                    ──────────
npm init                             python3 -m venv venv
                                     source venv/bin/activate
npm install express                  pip install django
package.json (auto-updated)          pip freeze > requirements.txt (manual)
node_modules/ (packages here)        venv/ (packages here)
npm install (from package.json)      pip install -r requirements.txt
```

**Key difference:** In Python, you create a "virtual environment" (venv) first. This is an isolated folder (like node_modules) so packages don't pollute your system Python. You must "activate" it before installing anything.

---

## 2. Project Structure Explained

```
danjo/                               Express Equivalent
├── venv/                            # node_modules/
├── manage.py                        # server.js (entry point)
├── .env                             # .env (same!)
├── .gitignore                       # .gitignore (same!)
├── requirements.txt                 # package.json (dependency list)
│
├── config/                          # Your app.js setup code
│   ├── __init__.py                  # (tells Python this is a package)
│   ├── settings.py                  # All configuration in one place:
│   │                                #   - installed apps (like require())
│   │                                #   - middleware (like app.use())
│   │                                #   - CORS settings
│   │                                #   - database (we skip this)
│   ├── urls.py                      # Root router: app.use('/api', tripRoutes)
│   ├── wsgi.py                      # For deployment (ignore for now)
│   └── asgi.py                      # For deployment (ignore for now)
│
├── trip/                            # A "feature module" — like routes/trip.js + controllers/trip.js
│   ├── __init__.py                  # (tells Python this is a package)
│   ├── urls.py                      # Router for /api/trip/* endpoints
│   ├── views.py                     # Controller logic (handles requests)
│   ├── serializers.py               # Validation schemas (like Joi/Zod)
│   ├── hos_engine.py                # Pure business logic (HOS rules)
│   ├── route_service.py             # External API calls (Nominatim, ORS)
│   ├── apps.py                      # App config (auto-generated, don't touch)
│   ├── models.py                    # Database models (empty — we don't use DB)
│   ├── admin.py                     # Admin panel config (empty — we don't use it)
│   └── tests.py                     # Tests (optional)
│
└── docs/                            # Our documentation
    ├── implementation-plan.md
    └── django-backend-guide.md      # THIS FILE
```

### How routing works: Express vs Django

**Express:**
```javascript
// server.js
const tripRoutes = require('./routes/trip');
app.use('/api/trip', tripRoutes);

// routes/trip.js
router.post('/plan', tripController.planTrip);
```

**Django:**
```python
# config/urls.py  (root router)
urlpatterns = [
    path('api/trip/', include('trip.urls')),
]

# trip/urls.py  (feature router)
urlpatterns = [
    path('plan', PlanTripView.as_view()),
]
```

Same idea — root router delegates to feature router.

### How a request flows

```
Express:                              Django:
────────                              ───────
Request hits server.js                Request hits config/urls.py
  → middleware runs (cors, json)        → middleware runs (CORS, etc.)
  → matches route /api/trip/plan        → matches URL pattern
  → calls controller function           → calls view function
  → controller uses req.body            → view uses request.data
  → calls service functions             → calls service functions
  → returns res.json({...})             → returns Response({...})
```

---

## 3. API Endpoints

We have **1 main endpoint**. That's it. Simple.

### POST /api/trip/plan

**What it does:** Takes trip details, calculates route + HOS schedule, returns everything.

**Request Body:**
```json
{
  "current_location": "Los Angeles, CA",
  "pickup_location": "Phoenix, AZ",
  "dropoff_location": "Dallas, TX",
  "current_cycle_hours": 20
}
```

**What happens inside:**
```
1. Validate inputs (serializer checks all 4 fields exist)
2. Geocode all 3 locations → get lat/lng for each
3. Get driving route: Current → Pickup → Dropoff
4. Run HOS engine → calculates full schedule with breaks/rests/fuel
5. Return JSON response
```

**Response Body:**
```json
{
  "total_miles": 1420,
  "total_driving_hours": 19.5,
  "total_days": 2,
  "route_geometry": [
    [34.0522, -118.2437],
    [34.0510, -118.2300],
    "... hundreds of lat/lng points forming the route line on map ..."
  ],
  "stops": [
    {
      "type": "start",
      "location": "Los Angeles, CA",
      "lat": 34.0522,
      "lng": -118.2437,
      "time": "6:00 AM",
      "day": 1
    },
    {
      "type": "pickup",
      "location": "Phoenix, AZ",
      "lat": 33.4484,
      "lng": -112.0740,
      "time": "12:00 PM",
      "day": 1,
      "duration_hrs": 1
    },
    {
      "type": "fuel",
      "location": "Tucson, AZ",
      "lat": 32.2226,
      "lng": -110.9747,
      "time": "4:00 PM",
      "day": 1,
      "duration_hrs": 0.5
    },
    {
      "type": "rest",
      "location": "El Paso, TX",
      "lat": 31.7619,
      "lng": -106.4850,
      "time": "5:30 PM",
      "day": 1,
      "duration_hrs": 10
    },
    {
      "type": "dropoff",
      "location": "Dallas, TX",
      "lat": 32.7767,
      "lng": -96.7970,
      "time": "3:00 PM",
      "day": 2,
      "duration_hrs": 1
    }
  ],
  "daily_logs": [
    {
      "day": 1,
      "date": "2026-02-13",
      "total_miles": 670,
      "segments": [
        {"status": "off_duty",  "start": 0,    "end": 6,    "note": "Off Duty"},
        {"status": "on_duty",   "start": 6,    "end": 6.5,  "note": "Pre-trip inspection, Los Angeles, CA"},
        {"status": "driving",   "start": 6.5,  "end": 12,   "note": "Driving to Phoenix, AZ"},
        {"status": "on_duty",   "start": 12,   "end": 13,   "note": "Pickup, Phoenix, AZ"},
        {"status": "off_duty",  "start": 13,   "end": 13.5, "note": "30-min break"},
        {"status": "driving",   "start": 13.5, "end": 16,   "note": "Driving to Tucson, AZ"},
        {"status": "on_duty",   "start": 16,   "end": 16.5, "note": "Fuel stop, Tucson, AZ"},
        {"status": "driving",   "start": 16.5, "end": 17.5, "note": "Driving to El Paso, TX"},
        {"status": "sleeper",   "start": 17.5, "end": 24,   "note": "Sleeper Berth, El Paso, TX"}
      ],
      "hours_summary": {
        "off_duty": 6.5,
        "sleeper": 6.5,
        "driving": 9.0,
        "on_duty": 2.0
      }
    },
    {
      "day": 2,
      "date": "2026-02-14",
      "total_miles": 750,
      "segments": [
        {"status": "sleeper",   "start": 0,    "end": 3.5,  "note": "Sleeper Berth (continued), El Paso, TX"},
        {"status": "on_duty",   "start": 3.5,  "end": 4,    "note": "Pre-trip inspection, El Paso, TX"},
        {"status": "driving",   "start": 4,    "end": 12,   "note": "Driving towards Dallas, TX"},
        {"status": "off_duty",  "start": 12,   "end": 12.5, "note": "30-min break"},
        {"status": "driving",   "start": 12.5, "end": 15,   "note": "Driving to Dallas, TX"},
        {"status": "on_duty",   "start": 15,   "end": 16,   "note": "Dropoff, Dallas, TX"},
        {"status": "off_duty",  "start": 16,   "end": 24,   "note": "Off Duty — Trip Complete"}
      ],
      "hours_summary": {
        "off_duty": 8.5,
        "sleeper": 3.5,
        "driving": 10.5,
        "on_duty": 1.5
      }
    }
  ],
  "cycle_summary": {
    "cycle_before": 20,
    "on_duty_this_trip": 23,
    "cycle_after": 43,
    "remaining": 27,
    "limit": 70
  }
}
```

---

## 4. Postman Testing Plan

### Test 1: Multi-Day Trip (Main Test)
```
POST http://localhost:8000/api/trip/plan
Content-Type: application/json

{
  "current_location": "Los Angeles, CA",
  "pickup_location": "Phoenix, AZ",
  "dropoff_location": "Dallas, TX",
  "current_cycle_hours": 20
}
```
**What to check:**
- [ ] Response returns 200 OK
- [ ] `total_miles` is roughly 1400 (depends on actual route)
- [ ] `total_days` is 2 (trip is too long for 1 day)
- [ ] `route_geometry` has lat/lng array (for map polyline)
- [ ] `stops` has 5 entries: start, pickup, fuel, rest, dropoff
- [ ] Day 1 segments sum to exactly 24.0 hours
- [ ] Day 2 segments sum to exactly 24.0 hours
- [ ] No driving segment is longer than 11 hours
- [ ] 30-min break appears after 8 hours of cumulative driving
- [ ] 10-hour rest (sleeper) appears between Day 1 and Day 2
- [ ] Fuel stop appears (total miles > 1000)
- [ ] `cycle_after` = 20 + on_duty_this_trip

### Test 2: Short Trip (Single Day)
```json
{
  "current_location": "San Francisco, CA",
  "pickup_location": "Sacramento, CA",
  "dropoff_location": "Reno, NV",
  "current_cycle_hours": 10
}
```
**What to check:**
- [ ] `total_days` is 1
- [ ] No sleeper berth needed (trip fits in one shift)
- [ ] Only 1 daily_log entry
- [ ] All segments sum to 24.0 hours

### Test 3: Near Cycle Limit
```json
{
  "current_location": "Los Angeles, CA",
  "pickup_location": "Phoenix, AZ",
  "dropoff_location": "Dallas, TX",
  "current_cycle_hours": 60
}
```
**What to check:**
- [ ] Driver can only work 10 more hours before hitting 70
- [ ] May need a 34-hour restart mid-trip
- [ ] Trip takes more days than Test 1

### Test 4: Validation Errors
```json
{
  "current_location": "",
  "pickup_location": "Phoenix, AZ"
}
```
**What to check:**
- [ ] Returns 400 Bad Request
- [ ] Error message says which fields are missing

### Test 5: Invalid Location
```json
{
  "current_location": "asdfghjkl",
  "pickup_location": "Phoenix, AZ",
  "dropoff_location": "Dallas, TX",
  "current_cycle_hours": 20
}
```
**What to check:**
- [ ] Returns error saying location could not be found
- [ ] Doesn't crash the server

---

## 5. HOS Engine — Deep Dive

### What is the HOS Engine?

It's a Python function that **simulates a truck driver's trip**. Think of it like a game loop:
- The "clock" ticks forward
- At each point, the engine checks: "Can the driver keep driving, or must they stop?"
- When a limit is hit, it inserts the right kind of break
- It records every status change (driving, resting, fueling) as a "segment"

### The 6 Rules (in priority order)

```
RULE 1: 70-Hour Cycle (weekly limit)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total on-duty hours (driving + on-duty not driving) across
the last 8 days cannot exceed 70 hours.

Example: Driver has already used 60 hours this week.
         They can only work 10 more hours total.
         After that → 34-hour restart (resets to 0).

Express analogy: Like a rate limiter — but instead of
requests/minute, it's work-hours/8-days.


RULE 2: 14-Hour Window (daily limit — the clock)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Once you start working, a 14-hour countdown begins.
After 14 hours from your first work activity, you CANNOT
drive — even if you only drove 5 hours out of 14.

The key: this clock does NOT pause for breaks or non-driving
work. It only resets after 10 consecutive hours off.

Example: Start at 6:00 AM → Window ends at 8:00 PM
         No matter what, NO driving after 8:00 PM.

Express analogy: Like a JWT token that expires in 14 hours.
Once issued, the clock ticks regardless of activity.


RULE 3: 11-Hour Driving Limit (daily driving cap)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Within that 14-hour window, you can drive a maximum
of 11 hours total. The other 3 hours can be non-driving
work (loading, inspecting, fueling, paperwork).

Example: Drive 5 hrs, load truck 1 hr, drive 6 hrs = 11 driving ✓
         Drive 5 hrs, load truck 1 hr, drive 7 hrs = 12 driving ✗

Express analogy: Rate limit within a rate limit.


RULE 4: 30-Minute Break (after 8 hours driving)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
After 8 cumulative hours of driving (not consecutive),
driver must take a 30-minute break before driving again.

Important: This is CUMULATIVE driving, not consecutive.
If you drive 4 hrs, take a 15-min fuel stop, drive 4 more
hrs — that's 8 hrs driving. 30-min break needed NOW.

The break resets the 8-hour counter back to 0.

Note: The fuel stop (15 min) did NOT count as the break
because it was only 15 min (needs to be 30+ consecutive).
But if the fuel stop was 30+ min, it WOULD count.


RULE 5: 10-Hour Off-Duty (between shifts)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Between shifts, driver must have 10 CONSECUTIVE hours
off duty (can be sleeper berth). This resets both the
11-hour driving limit and the 14-hour window.

Example: Stop driving at 5:30 PM
         10 hours off → Ready at 3:30 AM next day
         New 14-hour window: 3:30 AM → 5:30 PM
         New 11-hour driving limit: fresh


RULE 6: Fuel Every 1,000 Miles (assumption)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Not a legal rule, but an assessment requirement.
Stop for fuel every ~1,000 miles. Takes ~30 minutes.
This counts as on-duty not driving time.
```

### How the Engine Simulates the Trip — Step by Step

Imagine you're watching a driver on Day 1 of an LA → Phoenix → Dallas trip:

```
CLOCK   ACTION                           ENGINE STATE
─────   ──────                           ────────────
0:00    Midnight — Off Duty              off_duty segment starts
        (driver is sleeping)             driving_in_shift = 0
                                         duty_in_shift = 0
                                         driving_since_break = 0

6:00    Wake up — Pre-trip inspection    on_duty segment (0.5 hrs)
        Check tires, lights, brakes      duty_in_shift = 0.5
        THIS STARTS THE 14-HR WINDOW     shift_start = 6.0
                                         14hr window ends at 20:00

6:30    Start driving LA → Phoenix       driving segment starts
        Distance: 370 miles, ~5.5 hrs    driving_in_shift = 0
                                         driving_since_break = 0

12:00   Arrive Phoenix — Pickup          driving segment ends (5.5 hrs)
        Load the truck (1 hour)          driving_in_shift = 5.5
                                         driving_since_break = 5.5
                                         duty_in_shift = 6.0
                                         on_duty segment (1 hr)

13:00   Pickup done.                     duty_in_shift = 7.0
        Engine checks: 5.5 + future      driving_since_break = 5.5
        driving will hit 8 hrs soon.
        But can we drive 2.5 more hrs
        before the 8-hr break? YES.

        WAIT — actually the engine
        checks if a break makes sense
        here. We've been on-duty for 7
        hrs. 30-min break NOW means we
        reset the 8-hr driving counter.

        → Take 30-min break              off_duty segment (0.5 hrs)
                                         driving_since_break = 0 (RESET!)
                                         duty_in_shift = 7.5

13:30   Resume driving → towards Dallas  driving segment starts
        Need to go ~1050 miles
        At ~65 mph = ~16 hrs driving
        But we only have:
          11 - 5.5 = 5.5 hrs driving left
          14 - 7.5 = 6.5 hrs window left
          min(5.5, 6.5) = 5.5 hrs max

        But ALSO fuel: we've gone 370 mi
        Need fuel at 1000 mi mark
        1000 - 370 = 630 miles left
        At 65mph = ~9.7 hrs
        So fuel isn't the limit yet.

        Drive for how long?
        min(5.5, 6.5, 8.0, 9.7, 16) = 5.5

        → Drive 5.5 more hours           driving segment (5.5 hrs)

        BUT WAIT — at some point we hit
        1000 total miles. Let's say at
        ~4:00 PM (after 2.5 hrs driving)
        we've covered 370 + 163 + 467
        = 1000 miles

        → Engine splits the drive:
          Drive 2.5 hrs (13:30-16:00)
          Fuel stop 0.5 hrs (16:00-16:30)
          Drive remaining (16:30-...)

16:00   Fuel Stop — Tucson area          on_duty segment (0.5 hrs)
        30 min to refuel                  miles_since_fuel = 0 (RESET!)
                                         driving_in_shift = 8.0
                                         duty_in_shift = 10.5

16:30   Resume driving                   driving segment
        driving_in_shift = 8.0
        Can drive: 11 - 8 = 3 more hrs
        14hr window: 20:00 - 16:30 = 3.5
        8hr break: 8.0 already! WAIT—

        Oh no, driving_since_break is
        now 5.0 (2.5 + fuel doesn't
        reset it unless fuel was 30 min
        of OFF-DUTY)

        Fuel is ON-DUTY, so it doesn't
        count as the 30-min break.
        driving_since_break = 5.0
        Can drive: 8 - 5 = 3 more hrs

        min(3, 3, 3.5) = 3 hrs

        Actually let's simplify: engine
        drives 1 more hour

17:30   Hit 14-hr window limit            duty_in_shift = 11.5
        OR hit 11-hr driving limit         driving_in_shift = 9.0

        (In reality the exact numbers
        depend on precise calculation.
        The engine computes the exact
        minimum and stops there.)

        → 10-hour rest (Sleeper Berth)    sleeper segment starts
                                          sleeper until 3:30 AM next day

        Fill rest of day to midnight:     sleeper segment (17.5 → 24.0)

        === END DAY 1 ===                Save day 1 to daily_logs
        === START DAY 2 ===              New segments array

DAY 2:
0:00    Sleeper continues                 sleeper segment (0 → 3.5)
3:30    Wake up — 10 hrs rest done        ALL COUNTERS RESET:
        Pre-trip inspection               driving_in_shift = 0
                                         duty_in_shift = 0.5
                                         driving_since_break = 0
                                         shift_start = 3.5
                                         14hr window ends at 17:30

4:00    Drive towards Dallas              driving segment
        ~750 miles remaining
        At 65mph = ~11.5 hrs
        But can only drive 11 hrs max

        Drive 8 hrs → hit 30-min break

12:00   30-min break                      off_duty segment (0.5 hrs)
                                         driving_since_break = 0 (RESET!)

12:30   Resume driving                    driving segment
        Drive 2.5 more hrs

15:00   Arrive Dallas — Dropoff           on_duty segment (1 hr)
        Unload truck

16:00   Trip Complete — Off Duty          off_duty segment (16 → 24)

        === END DAY 2 ===                Save day 2 to daily_logs
```

### Engine Data Structures

```python
# What the engine tracks internally (state object)
state = {
    "current_time": 6.0,          # Hours since midnight (6.0 = 6:00 AM)
    "current_day": 1,             # Day counter
    "shift_driving": 0,           # Driving hours in current shift (max 11)
    "shift_duty": 0,              # Total duty hours in current shift (max 14)
    "driving_since_break": 0,     # Driving since last 30-min break (max 8)
    "cycle_hours": 20,            # Total on-duty in last 8 days (max 70)
    "miles_since_fuel": 0,        # Miles since last fuel (max 1000)
    "total_miles_driven": 0,      # Total trip miles so far
    "segments": [],               # Current day's log segments
    "daily_logs": [],             # Completed days
    "stops": [],                  # Map marker data
}

# What a segment looks like
segment = {
    "status": "driving",          # driving | on_duty | off_duty | sleeper
    "start": 6.5,                 # Start time (hours since midnight)
    "end": 12.0,                  # End time (hours since midnight)
    "note": "Driving to Phoenix, AZ"
}

# What a stop looks like (for map markers)
stop = {
    "type": "fuel",               # start | pickup | fuel | rest | dropoff
    "location": "Tucson, AZ",
    "lat": 32.2226,
    "lng": -110.9747,
    "time": "4:00 PM",
    "day": 1,
    "duration_hrs": 0.5
}
```

### Key Edge Cases the Engine Must Handle

```
1. MIDNIGHT CROSSOVER
   Driver is sleeping from 5:30 PM to 3:30 AM.
   Day 1 gets: sleeper segment 17.5 → 24.0 (6.5 hrs)
   Day 2 gets: sleeper segment 0.0 → 3.5 (3.5 hrs)
   Total rest: 10 hrs ✓

2. FUEL + BREAK OVERLAP
   If fuel stop happens right when 30-min break is due,
   and the fuel takes 30+ min → it counts as the break too!
   Two birds, one stone. Engine should check this.

3. PICKUP/DROPOFF TIMING
   Pickup/dropoff is ON-DUTY not driving.
   It counts towards the 14-hr window and 70-hr cycle,
   but NOT towards the 11-hr driving limit.

4. CYCLE EXHAUSTION
   If cycle_hours is 68, driver can only do 2 more hrs
   of on-duty work. If the trip needs 20 hrs on-duty,
   the driver must take a 34-hr restart mid-trip.
   34 hrs off → cycle resets to 0 → 70 hrs available again.

5. EACH DAY MUST SUM TO 24.0 HOURS
   off_duty + sleeper + driving + on_duty = 24.0
   Always. No exceptions. If driver finishes at 4 PM,
   fill 4 PM → midnight with off_duty.
```

---

## 6. External API Calls

### Nominatim (Geocoding) — No API Key Needed
Converts a city name to lat/lng coordinates.

```
GET https://nominatim.openstreetmap.org/search?q=Los+Angeles,+CA&format=json&limit=1

Response:
[{
  "lat": "34.0536909",
  "lon": "-118.242766",
  "display_name": "Los Angeles, Los Angeles County, California, United States"
}]
```

**Important:** Nominatim has a rate limit of 1 request/second. Add a small delay between calls.

### OpenRouteService (Routing) — Free API Key Required
Gets driving route between two points.

```
GET https://api.openrouteservice.org/v2/directions/driving-hgv?api_key=YOUR_KEY&start=-118.24,34.05&end=-112.07,33.44

Response:
{
  "features": [{
    "properties": {
      "summary": {
        "distance": 595427,    ← meters (divide by 1609 for miles)
        "duration": 19800      ← seconds (divide by 3600 for hours)
      }
    },
    "geometry": {
      "coordinates": [         ← array of [lng, lat] points for map
        [-118.24, 34.05],
        [-118.23, 34.04],
        ...
      ]
    }
  }]
}
```

**Note:** We use `driving-hgv` (heavy goods vehicle = truck) not `driving-car` for more accurate truck routes.

**We make 2 route calls:**
1. Current Location → Pickup Location (leg 1)
2. Pickup Location → Dropoff Location (leg 2)

Or 1 call with waypoints if ORS supports it.

---

## 7. Setup Steps (What We'll Do First)

```bash
# Step 1: Go to project directory
cd /Users/oscarmandeep/Documents/assessments/danjo

# Step 2: Create virtual environment
python3 -m venv venv

# Step 3: Activate it (you'll see (venv) in your terminal)
source venv/bin/activate

# Step 4: Install all packages
pip install django djangorestframework django-cors-headers python-decouple requests

# Step 5: Create Django project (config is the project name)
django-admin startproject config .

# Step 6: Create the trip app
python manage.py startapp trip

# Step 7: Save dependencies
pip freeze > requirements.txt

# Step 8: Create .env file
echo "ORS_API_KEY=your_key_here" > .env

# Step 9: Run migrations (Django needs this even without models)
python manage.py migrate

# Step 10: Start the server!
python manage.py runserver
# Server runs at http://localhost:8000
```

After Step 10, visit http://localhost:8000 — you should see the Django welcome page. Then we start coding the actual API.

---

## 8. Quick Reference — Commands You'll Use Often

| What | Command | Express Equivalent |
|------|---------|-------------------|
| Start server | `python manage.py runserver` | `npm run dev` / `node server.js` |
| Install package | `pip install <package>` | `npm install <package>` |
| Save deps | `pip freeze > requirements.txt` | (auto in package.json) |
| Install from file | `pip install -r requirements.txt` | `npm install` |
| Activate venv | `source venv/bin/activate` | (no equivalent) |
| Deactivate venv | `deactivate` | (no equivalent) |
| Create app | `python manage.py startapp <name>` | (manually create folder) |
| Run migrations | `python manage.py migrate` | (no equivalent — we don't use DB) |
| Django shell | `python manage.py shell` | `node` (REPL) |
