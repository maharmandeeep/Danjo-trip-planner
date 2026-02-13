# Spotter ELD Trip Planner — Full Implementation Plan

---

## TREE 1: What We're Building (From All Docs)

### The App in One Line
A truck driver enters trip details -> app calculates the route following legal driving rules -> generates filled-out daily log sheets + route map.

### Inputs (4 fields)
1. **Current Location** — where driver is now (e.g., "Los Angeles, CA")
2. **Pickup Location** — where they get the load (e.g., "Phoenix, AZ")
3. **Dropoff Location** — final delivery (e.g., "Dallas, TX")
4. **Current Cycle Used** — hours already worked in last 8 days out of 70 max (e.g., 20)

### Outputs (3 things)
1. **Route Map** — interactive map showing the full route with colored pins for each stop (start, pickup, fuel, rest, dropoff)
2. **Daily Log Sheets** — paper-style log forms with graph grid showing colored horizontal lines for when driver is Driving, On Duty, Off Duty, or in Sleeper Berth
3. **Trip Summary** — total miles, hours breakdown, 70-hour cycle progress bar

### HOS Rules We Must Implement (from FMCSA PDF)
| Rule | What It Means |
|------|--------------|
| 11-hour driving limit | Can't drive more than 11 hrs in one shift |
| 14-hour window | Can't drive after 14 hrs from when shift started (even if not all driving) |
| 30-min break | Must take 30-min break after 8 hrs of cumulative driving |
| 10-hour off-duty | Must rest 10 consecutive hours between shifts |
| 70hr/8day cycle | Total on-duty time can't exceed 70 hrs in rolling 8-day period |
| 34-hour restart | 34 consecutive hrs off resets the 70hr cycle to zero |
| Fuel every 1,000 mi | Stop for fuel ~30 min every 1,000 miles |
| 1 hr pickup/dropoff | Loading/unloading counts as on-duty not driving |

### API We're Building
```
POST /api/trip/plan

Request:  { current_location, pickup_location, dropoff_location, current_cycle_hours }
Response: { total_miles, total_driving_hours, total_days, route_geometry, stops[], daily_logs[], cycle_summary }
```

### Full API Response Example
```json
{
  "total_miles": 1420,
  "total_driving_hours": 19.5,
  "total_days": 2,
  "route_geometry": [[lat, lng], ...],
  "stops": [
    {"type": "start", "location": "Los Angeles, CA", "lat": 34.05, "lng": -118.24},
    {"type": "pickup", "location": "Phoenix, AZ", "lat": 33.44, "lng": -112.07, "duration_hrs": 1},
    {"type": "fuel", "location": "Tucson, AZ", "lat": 32.22, "lng": -110.92},
    {"type": "rest", "location": "El Paso, TX", "lat": 31.76, "lng": -106.44, "duration_hrs": 10},
    {"type": "dropoff", "location": "Dallas, TX", "lat": 32.77, "lng": -96.79, "duration_hrs": 1}
  ],
  "daily_logs": [
    {
      "day": 1,
      "date": "2026-02-10",
      "total_miles": 670,
      "segments": [
        {"status": "off_duty", "start": 0, "end": 6},
        {"status": "on_duty", "start": 6, "end": 6.5, "note": "Pre-trip, Los Angeles, CA"},
        {"status": "driving", "start": 6.5, "end": 12},
        {"status": "on_duty", "start": 12, "end": 13, "note": "Pickup, Phoenix, AZ"},
        {"status": "off_duty", "start": 13, "end": 13.5, "note": "30-min break"},
        {"status": "driving", "start": 13.5, "end": 16},
        {"status": "on_duty", "start": 16, "end": 16.5, "note": "Fuel, Tucson, AZ"},
        {"status": "driving", "start": 16.5, "end": 17.5},
        {"status": "sleeper", "start": 17.5, "end": 24, "note": "Rest, El Paso, TX"}
      ]
    },
    {
      "day": 2,
      "date": "2026-02-11",
      "total_miles": 750,
      "segments": [...]
    }
  ],
  "cycle_summary": {
    "cycle_before": 20,
    "on_duty_this_trip": 23,
    "cycle_after": 43,
    "remaining": 27
  }
}
```

### External APIs We Call (all free)
- **Nominatim** — converts "Dallas, TX" -> lat/lng coordinates (geocoding)
- **OpenRouteService** — driving route, distance, duration between coordinates (needs free API key)

---

## TREE 2: Django Backend Plan

### Django <-> Express Cheat Sheet
| Express (you know this) | Django Equivalent |
|------------------------|-------------------|
| `npm init` | `django-admin startproject config .` |
| `package.json` | `requirements.txt` |
| `node_modules/` | `venv/` (virtual environment) |
| `npm install express` | `pip install django` |
| `app.js` / `server.js` | `manage.py` (entry point) |
| `routes/trip.js` | `trip/urls.py` |
| `controllers/tripController.js` | `trip/views.py` |
| Express Router | Django URL patterns |
| `req.body` | `request.data` (with DRF) |
| `res.json({...})` | `Response({...})` |
| Middleware (cors, json parser) | Django middleware (CORS, etc.) |
| `app.listen(8000)` | `python manage.py runserver` |
| `.env` file | `.env` file (same concept, use python-decouple) |
| Joi / Zod validation | DRF Serializers |

### Backend Folder Structure
```
danjo/
├── venv/                    # Virtual environment (like node_modules)
├── manage.py                # Entry point (like node server.js)
├── config/                  # Project config (like your app.js setup)
│   ├── settings.py          # All config: DB, CORS, installed apps
│   ├── urls.py              # Root URL router (like app.use('/api', routes))
│   └── wsgi.py              # For deployment
├── trip/                    # Our main app (like a feature module)
│   ├── views.py             # API endpoint logic (like controllers)
│   ├── urls.py              # Trip-specific routes
│   ├── hos_engine.py        # HOS calculation logic (core algorithm)
│   ├── route_service.py     # Nominatim + OpenRouteService API calls
│   └── serializers.py       # Request/response validation (like Joi schemas)
├── docs/                    # Documentation
│   └── implementation-plan.md
├── requirements.txt         # Dependencies list (like package.json)
├── .env                     # API keys
└── .gitignore
```

### Phase B1: Project Setup
1. Create virtual environment: `python3 -m venv venv`
2. Activate it: `source venv/bin/activate`
3. Install dependencies: `pip install django djangorestframework django-cors-headers python-decouple requests`
4. Create Django project: `django-admin startproject config .`
5. Create trip app: `python manage.py startapp trip`
6. Configure settings.py (add DRF, CORS, trip app)
7. Set up URL routing
8. Create .env with OpenRouteService API key
9. Save requirements.txt: `pip freeze > requirements.txt`

### Phase B2: route_service.py — External API Calls
**File: `trip/route_service.py`**

Two functions:
1. `geocode(location_name)` -> calls Nominatim -> returns `{lat, lng}`
2. `get_route(coordinates_list)` -> calls OpenRouteService -> returns `{distance_miles, duration_hours, geometry}`

The route is: Current -> Pickup -> Dropoff (two legs).

### Phase B3: hos_engine.py — The Core Algorithm (Most Complex Part)
**File: `trip/hos_engine.py`**

This is the brain of the app. It simulates the driver's trip hour-by-hour and decides when they must stop.

**Algorithm pseudocode:**
```
function calculate_trip(route_legs, current_cycle_hours):

    state = {
        current_time: 6.0 (6:00 AM start),
        shift_start: 6.0,
        driving_hours_in_shift: 0,
        duty_hours_in_shift: 0,        # time since 10hr rest (14hr window)
        driving_since_break: 0,         # for 30-min break rule (8hr limit)
        cycle_hours: current_cycle_hours,  # 70hr tracker
        miles_since_fuel: 0,
        current_day: 1,
        segments: [],                   # log entries for current day
        daily_logs: [],                 # completed days
        stops: []                       # map markers
    }

    # Step 1: Pre-trip inspection (30 min on-duty)
    add_segment("on_duty", 0.5, "Pre-trip inspection")

    # Step 2: Process each route leg
    for each leg in [current->pickup, pickup->dropoff]:
        remaining_drive_hours = leg.duration
        remaining_miles = leg.distance

        while remaining_drive_hours > 0:
            # Calculate how long we can drive before hitting ANY limit
            max_drive = min(
                11 - driving_hours_in_shift,          # 11hr driving limit
                14 - duty_hours_in_shift,              # 14hr window
                8 - driving_since_break,               # 30min break needed
                70 - cycle_hours (converted to drive),  # 70hr cycle
                hours_until_1000_miles,                 # fuel stop
                remaining_drive_hours                   # remaining distance
            )

            if max_drive <= 0:
                # Must take a break — figure out which one
                if driving_since_break >= 8:
                    take_30min_break()
                elif driving_hours_in_shift >= 11 OR duty_hours_in_shift >= 14:
                    take_10hr_rest()  # sleeper berth, new day
                elif cycle_hours >= 70:
                    take_34hr_restart()
            else:
                # Drive for max_drive hours
                add_segment("driving", max_drive)
                update all counters

            if hit fuel stop (1000 miles):
                add_segment("on_duty", 0.5, "Fuel stop")

        # At pickup/dropoff: 1 hour on-duty
        if leg == pickup_leg:
            add_segment("on_duty", 1.0, "Pickup")
        elif leg == dropoff_leg:
            add_segment("on_duty", 1.0, "Dropoff")

    # Step 3: Fill remaining hours of last day as off-duty
    # Step 4: Return { stops, daily_logs, cycle_summary }
```

**Key helper functions:**
- `add_segment(status, duration, note)` — adds to current day's segments, handles day boundary (midnight crossover)
- `take_30min_break()` — adds off_duty segment of 0.5 hrs
- `take_10hr_rest()` — fills rest of current day as sleeper, starts new day
- `take_34hr_restart()` — similar but 34 hrs, resets cycle to 0
- `calculate_location_at_time()` — interpolates position along route for stop coordinates

### Phase B4: views.py — API Endpoint
**File: `trip/views.py`**

Single endpoint that:
1. Receives POST with 4 inputs
2. Calls `geocode()` for each location
3. Calls `get_route()` for the full path
4. Calls `calculate_trip()` (HOS engine)
5. Returns JSON response

### Phase B5: Postman/curl Testing
Test with sample data:
- LA -> Phoenix -> Dallas (multi-day trip)
- Short trip (single day)
- High cycle hours (near 70hr limit)
- Edge cases (exactly at limits)

---

## TREE 3: Next.js Frontend Plan

### Why Next.js
- Deploys to Vercel in one click (assessment requires hosted version)
- App Router gives file-based routing
- Learn essential Next.js patterns while building

### Next.js <-> Express/React Cheat Sheet
| Express/React (you know) | Next.js Equivalent |
|--------------------------|-------------------|
| `react-router` routes | `app/` folder = automatic routes |
| `pages/Home.jsx` | `app/page.jsx` (home page) |
| `components/` folder | `app/components/` (same idea) |
| `useEffect` fetch on mount | Client Component with `"use client"` |
| `.env` vars | `.env.local` with `NEXT_PUBLIC_` prefix for client vars |
| `npm run dev` | `npm run dev` (same!) |
| Express API routes | `app/api/route.js` (optional, we use Django) |

### Frontend Folder Structure
```
react/
├── app/                         # Next.js App Router
│   ├── layout.jsx               # Root layout (wraps all pages)
│   ├── page.jsx                 # Home page — the main trip planner UI
│   ├── globals.css              # Tailwind imports
│   └── components/              # All our components
│       ├── TripForm.jsx         # Input form (4 fields + submit)
│       ├── RouteMap.jsx         # Leaflet map with route + markers
│       ├── LogSheet.jsx         # Canvas/SVG daily log grid (hardest part)
│       ├── Timeline.jsx         # Trip schedule timeline
│       └── TripSummary.jsx      # Stats cards + cycle progress bar
├── lib/
│   └── api.js                   # Fetch calls to Django backend
├── public/                      # Static files
├── package.json
├── next.config.js
├── tailwind.config.js
├── postcss.config.js
└── .env.local                   # NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Phase F1: Project Setup
1. `npx create-next-app@latest . --tailwind --eslint --app --src-dir=false`
2. Install deps: `npm install react-leaflet leaflet`
3. Set up `lib/api.js` with base URL from env
4. Create `.env.local`

### Key Next.js Concepts
- **`"use client"`** — Leaflet and form components need this (they use browser APIs)
- **`app/page.jsx`** — single-page app, all components render here
- **`layout.jsx`** — wraps everything, great for nav bar and global styles
- **Dynamic imports** — Leaflet: `dynamic(() => import(...), { ssr: false })`

### Phase F2-F5: Components
- **TripForm** — 4 inputs + submit button
- **RouteMap** — Leaflet map, route polyline, colored stop markers
- **LogSheet** — Canvas/SVG daily log grid (hardest part)
- **Timeline** — vertical event list with colored dots
- **TripSummary** — stat cards + 70hr cycle progress bar

### Phase F6-F7: Integration & Polish
- Wire components in page.jsx
- Loading states, error handling
- Responsive + dark theme

---

## Pre-Requisite: Get OpenRouteService API Key
1. Go to https://openrouteservice.org/dev/#/signup
2. Sign up for free account
3. Dashboard -> Request a Token
4. Copy the API key
5. Free tier: 2,500 requests/day

---

## Implementation Order

### BACKEND FIRST (test with Postman/curl)
| Step | What | Files |
|------|------|-------|
| B1 | Django project setup + venv + deps + CORS | config/, manage.py, requirements.txt, .env |
| B2 | route_service.py (geocoding + routing) | trip/route_service.py |
| B3 | hos_engine.py (HOS calculation) | trip/hos_engine.py |
| B4 | views.py + urls.py (API endpoint) | trip/views.py, trip/urls.py, config/urls.py |
| B5 | Test with curl/Postman | -- |

### THEN NEXT.JS FRONTEND
| Step | What | Files |
|------|------|-------|
| F1 | Next.js + Tailwind setup | package.json, next.config.js |
| F2 | TripForm component | app/components/TripForm.jsx |
| F3 | RouteMap component (Leaflet) | app/components/RouteMap.jsx |
| F4 | LogSheet component (Canvas/SVG) | app/components/LogSheet.jsx |
| F5 | Timeline + Summary | app/components/Timeline.jsx, TripSummary.jsx |
| F6 | Wire everything in page.jsx | app/page.jsx, lib/api.js |
| F7 | Polish + responsive + dark theme | -- |

### DEPLOYMENT
| Step | What |
|------|------|
| D1 | Deploy Django to Railway or Render (free) |
| D2 | Deploy Next.js to Vercel (one-click from GitHub) |
| D3 | Record 3-5 min Loom video |

---

## Verification / Testing Plan
1. **Backend:** POST to `/api/trip/plan` with LA -> Phoenix -> Dallas, cycle=20
2. **HOS check:** No driving segment > 11hrs, no shift > 14hrs, 30-min breaks after 8hrs driving
3. **Fuel check:** Fuel stop every ~1000 miles
4. **Log check:** Each day's segments sum to 24.0 hours
5. **Cycle check:** cycle_before + on_duty_this_trip = cycle_after
6. **Frontend:** Map shows correct route, log grids match wireframe, all stops on timeline
7. **Cross-browser:** Chrome + Safari
