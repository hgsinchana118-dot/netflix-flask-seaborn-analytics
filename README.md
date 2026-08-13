# Netflix Movie & TV Show Data Analytics (Flask + seaborn)

A Flask web app that analyzes Netflix-style content data and renders
seaborn/matplotlib charts in a dark, Netflix-themed dashboard. Ships with a
1,200-row synthetic dataset so it works out of the box, and lets you upload
your own `netflix_titles.csv` (e.g. the Kaggle "Netflix Movies and TV Shows"
dataset) to re-run every chart on your real data.

## Features

- **Dashboard** — summary stat cards (title counts, top genre/country/rating, etc.)
- **8 seaborn charts**, each generated server-side and served as PNG:
  - Movies vs TV Shows
  - Top Genres
  - Releases Over Time (by type)
  - Content Rating Distribution
  - Top Content-Producing Countries
  - Movie Duration Histogram
  - Titles Added to Netflix by Year
  - Genre vs Rating Heatmap
- **CSV upload** — swap in your own dataset (validated for required columns);
  session-scoped so different browser sessions don't clobber each other
- **Downloads** — every chart is downloadable as a standalone PNG; the active
  dataset is downloadable as CSV
- **Data preview table** of the first 10 rows

## Project structure

```
netflix_app/
├── app.py                  # Flask routes
├── analytics.py            # pandas loading + seaborn chart functions
├── requirements.txt
├── data/
│   ├── generate_data.py    # synthetic dataset generator
│   └── netflix_titles.csv  # generated sample dataset (1200 rows)
├── uploads/                 # user-uploaded CSVs land here
└── templates/
    └── index.html          # dashboard UI
```

## Setup

```bash
cd netflix_app
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open **http://127.0.0.1:5000**.

## Using your own data

Upload a CSV with (at minimum) these columns, matching the common Kaggle
Netflix dataset schema:

```
type, release_year, listed_in, country, rating, duration, date_added
```

The app validates the required columns on upload and will flag anything
missing. Click **Reset to Sample Data** to go back to the synthetic dataset.

## Regenerating the synthetic dataset

```bash
python data/generate_data.py
```

Edit `data/generate_data.py` to change row count, genres, countries, rating
weights, etc.

## Notes

- Charts are rendered fresh on each request (not cached), so they always
  reflect the currently active dataset. For heavy production traffic you'd
  want to cache PNGs (e.g. per dataset hash) rather than regenerate on every
  page load.
- Uses Matplotlib's `Agg` backend, which is required for headless/server-side
  chart rendering.
- This is a Flask **development server** — for production, run behind
  gunicorn/uWSGI + nginx and set a real `SECRET_KEY`.
