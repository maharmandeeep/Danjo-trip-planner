# Spotter ELD Trip Planner - Backend API

A Django REST API that calculates optimal truck driver routes while respecting **FMCSA Hours-of-Service (HOS)** regulations. Given a current location, pickup, and dropoff, it returns a complete trip plan with stops, daily ELD logs, and route geometry.

## Features

- Geocoding via Nominatim (OpenStreetMap)
- Truck routing via OpenRouteService (HGV profile)
- Full HOS compliance engine:
  - 70-hour / 8-day cycle limit
  - 14-hour on-duty window
  - 11-hour driving limit
  - 30-minute break after 8 hours driving
  - 10-hour off-duty rest between shifts
  - Fuel stops every 1,000 miles
- Daily ELD log generation with segment breakdowns
- Route geometry for map display

## Tech Stack

- **Python 3.9** / **Django 4.2** / **Django REST Framework**
- **Gunicorn** (production WSGI server)
- **WhiteNoise** (static file serving)
- **python-decouple** (environment variable management)

## API Endpoint

### `POST /api/trip/plan`

**Request Body:**
```json
{
  "current_location": "Los Angeles, CA",
  "pickup_location": "Phoenix, AZ",
  "dropoff_location": "Dallas, TX",
  "current_cycle_hours": 20
}
```

| Field                | Type   | Description                                      |
|----------------------|--------|--------------------------------------------------|
| `current_location`   | string | Driver's current location                        |
| `pickup_location`    | string | Pickup address                                   |
| `dropoff_location`   | string | Dropoff/delivery address                         |
| `current_cycle_hours`| number | Hours already used in the 70-hour cycle (0-70)   |

**Response** (200 OK):
```json
{
  "total_miles": 1420,
  "total_driving_hours": 19.5,
  "total_days": 2,
  "route_geometry": [[lat, lng], ...],
  "stops": [
    {"type": "start", "location": "Los Angeles, CA", "lat": 34.05, "lng": -118.24},
    {"type": "pickup", "location": "Phoenix, AZ", "duration_hrs": 1},
    {"type": "fuel", "location": "Near I-10, AZ"},
    {"type": "rest", "location": "Rest area", "duration_hrs": 10},
    {"type": "dropoff", "location": "Dallas, TX", "duration_hrs": 1}
  ],
  "daily_logs": [
    {
      "day": 1,
      "date": "2026-02-14",
      "total_miles": 670,
      "segments": [
        {"status": "off_duty", "start": 0, "end": 6, "note": "Off Duty"},
        {"status": "driving", "start": 6.5, "end": 12, "note": "Driving to Phoenix, AZ"}
      ],
      "hours_summary": {"off_duty": 6.5, "sleeper": 6.5, "driving": 9.0, "on_duty": 2.0}
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

## Project Structure

```
danjo/
├── config/                 # Django project configuration
│   ├── settings.py         # Settings (env-driven for production)
│   ├── urls.py             # Root URL router
│   └── wsgi.py             # WSGI entry point
├── trip/                   # Trip planner app
│   ├── views.py            # API endpoint (PlanTripView)
│   ├── route_service.py    # Geocoding + routing (Nominatim + ORS)
│   └── hos_engine.py       # HOS calculation engine
├── docs/                   # Documentation
├── build.sh                # Render build script
├── render.yaml             # Render deployment blueprint
├── requirements.txt        # Python dependencies
└── manage.py               # Django CLI
```

## Local Development Setup

### Prerequisites

- Python 3.9+
- A free [OpenRouteService API key](https://openrouteservice.org/dev/#/signup)

### Steps

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd danjo
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS/Linux
   venv\Scripts\activate      # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` file** in the project root:
   ```
   ORS_API_KEY=your_openrouteservice_api_key_here
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

6. **Test the API:**
   ```bash
   curl -X POST http://localhost:8000/api/trip/plan \
     -H "Content-Type: application/json" \
     -d '{
       "current_location": "Los Angeles, CA",
       "pickup_location": "Phoenix, AZ",
       "dropoff_location": "Dallas, TX",
       "current_cycle_hours": 20
     }'
   ```

## Deploy to Render

### Option 1: Using the Blueprint (render.yaml)

1. Push your code to a GitHub repository.
2. Go to [Render Dashboard](https://dashboard.render.com).
3. Click **New** > **Blueprint**.
4. Connect your GitHub repo - Render will detect `render.yaml` automatically.
5. Set the **ORS_API_KEY** environment variable when prompted.
6. Click **Apply** - Render will build and deploy automatically.

### Option 2: Manual Setup

1. Push your code to a GitHub repository.

2. Go to [Render Dashboard](https://dashboard.render.com) and click **New** > **Web Service**.

3. Connect your GitHub repo.

4. Configure the service:
   | Setting        | Value                              |
   |----------------|------------------------------------|
   | **Runtime**    | Python                             |
   | **Build Command** | `./build.sh`                    |
   | **Start Command** | `gunicorn config.wsgi:application` |

5. Add the following **Environment Variables**:
   | Key              | Value                                |
   |------------------|--------------------------------------|
   | `SECRET_KEY`     | *(click Generate)*                   |
   | `DEBUG`          | `False`                              |
   | `ORS_API_KEY`    | *(your OpenRouteService API key)*    |
   | `PYTHON_VERSION` | `3.9.18`                             |

6. Click **Create Web Service**. Render will build and deploy your app.

7. Your API will be available at:
   ```
   https://your-service-name.onrender.com/api/trip/plan
   ```

### After Deployment

Test your live API:
```bash
curl -X POST https://your-service-name.onrender.com/api/trip/plan \
  -H "Content-Type: application/json" \
  -d '{
    "current_location": "Los Angeles, CA",
    "pickup_location": "Phoenix, AZ",
    "dropoff_location": "Dallas, TX",
    "current_cycle_hours": 20
  }'
```

## HOS Rules Implemented

| Rule                  | Limit                                      |
|-----------------------|--------------------------------------------|
| 70-Hour Cycle         | Max 70 on-duty hours in rolling 8 days     |
| 14-Hour Window        | No driving after 14 hrs from shift start   |
| 11-Hour Driving       | Max 11 hours driving per shift             |
| 30-Minute Break       | Required after 8 hours cumulative driving  |
| 10-Hour Off-Duty      | Between shifts (resets driving limits)     |
| Fuel Stop             | Every 1,000 miles (30 min each)            |

## License

MIT
