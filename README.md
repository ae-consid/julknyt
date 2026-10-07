# Julknyt 🎄

A small Flask app for planning a Christmas potluck. Create an event, share the link, and guests claim dishes.

Stack: Flask, Jinja2, HTMX, SQLite (Flask-SQLAlchemy), Pico.css.

## Run

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows (macOS/Linux: source .venv/bin/activate)
pip install -r requirements.txt
flask --app wsgi run --debug
```

Set `SECRET_KEY` (and optionally `DATABASE_URL`) in production.

## Test

```bash
pytest
```
