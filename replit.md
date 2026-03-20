# TurmasUnB

A web platform for University of Brasília (UnB) students to find and share online class meeting links (Google Meet, Teams, etc.) for their specific course sections ("turmas").

## Tech Stack

- **Backend/Frontend:** Python FastAPI serving Jinja2 HTML templates
- **Styling:** Tailwind CSS + DaisyUI (via CDN)
- **Data Storage:** `data.json` flat-file JSON database
- **Scraper:** Playwright (optional, separate requirements)
- **Server:** Uvicorn ASGI server

## Project Structure

- `main.py` - FastAPI app entry point; handles routing and API endpoints
- `templates/index.html` - Single-page frontend with search and link submission
- `data.json` - Persistent storage for all class data and links
- `scraper.py` - Optional Playwright-based SIGAA scraper to refresh data
- `extractor.js` - Browser console utility for manual data extraction
- `requirements.txt` - Core web server dependencies
- `requirements-scraper.txt` - Optional scraper dependencies

## Running

The app runs via the "Start application" workflow:
```
uvicorn main:app --host 0.0.0.0 --port 5000
```

## Key Endpoints

- `GET /` - Main search interface (HTML)
- `POST /` - Submit/update a class meeting link
- `GET /json` - Raw JSON of all class data

## Data Refresh

To update class data from SIGAA:
```
pip install -r requirements-scraper.txt
python scraper.py --periodo 2026.1
```

## Deployment Notes

- Uses VM deployment target to preserve `data.json` state between requests
- Host set to `0.0.0.0` with TrustedHostMiddleware allowing all hosts for Replit proxy compatibility
