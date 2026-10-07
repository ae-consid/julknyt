# Julknyt

## Project description
Julknyt is a small web app for planning a Christmas potluck. A host creates an event and shares its link. Guests open the link, see which dishes are planned, and add, claim, unclaim or remove dishes so nobody ends up bringing the same thing. There are no user accounts: access is through an unguessable share token in the URL, and guests identify themselves by typing a name.

The UI is in **Swedish only** (no language switcher). Stored values stay English keys (`Dish.category` such as `Main`, `Event.theme` such as `christmas`); Swedish labels live in `CATEGORY_LABELS` / `THEMES` in `app/models.py`. Dates use the `sv_date` filter (`app/format.py`), and WTForms validation messages are Swedish via `BaseForm.Meta.locales` in `app/forms.py`. Write new user-facing text in Swedish.

Keep it simple. This is a small app for a handful of people, not a platform.

## Tech stack
- **Python 3.14**, **Flask 3** with an application factory (`create_app` in `app/__init__.py`) and a single blueprint (`app/routes.py`)
- **Jinja2** server-rendered templates in `app/templates/`; `_dishes.html` is the partial that HTMX swaps
- **HTMX** (CDN) for interactivity without a JS framework; CSRF token is sent via `hx-headers` on `<body>`
- **SQLite** through **Flask-SQLAlchemy**; the DB file lives in `instance/` (git-ignored); tables are created with `db.create_all()` (no migrations yet)
- **Flask-WTF** for forms, validation and CSRF protection
- **Pico.css** (CDN) for styling
- **pytest** for tests, **gunicorn** for production (`wsgi.py` is the entry point)
- Dependencies are in `requirements.txt`; use the local `.venv`

### Commands
```bash
.venv\Scripts\flask --app wsgi run --debug   # dev server
.venv\Scripts\python -m pytest -q            # tests
```

## Architectural principles
- **Server-rendered first.** Return HTML, not JSON. HTMX requests (`HX-Request` header) get the `_dishes.html` partial; plain form posts redirect, so the app works without JavaScript.
- **Thin routes.** Routes parse input, call a model or helper, and render. If logic grows beyond a few lines, move it out of `routes.py` into a small service module rather than growing the route.
- **Scope everything to an event.** Every dish lookup must verify it belongs to the event identified by the URL token (see `_get_dish`). Never fetch a dish by id alone.
- **Validate at the boundary.** Use WTForms for user input, and keep length limits in sync with the model columns.
- **Keep CSRF on.** Every POST form needs the token, including HTMX forms. Don't exempt routes from `CSRFProtect`.
- **Config via environment.** `SECRET_KEY` and `DATABASE_URL` come from env vars; no secrets in code.
- **Small, reversible steps.** Prefer boring, minimal solutions over new abstractions. If the schema needs to change, introduce Flask-Migrate first instead of editing the models and hoping `create_all()` copes.
- **Test behavior.** Add a pytest test for each new route or rule. Tests use an in-memory SQLite DB with CSRF disabled (see `tests/test_app.py`).

## Limits for the agent
- **Stay in scope.** Make only the changes the user asked for. Don't refactor, rename or reformat unrelated code.
- **Ask before adding dependencies**, a JS build step, a frontend framework, user accounts or a different database. The stack choice is deliberate.
- **Never touch secrets or data.** Don't read or commit `.env` or `instance/`, and don't delete or reset the database file without asking.
- **Don't run destructive or outward-facing commands** without confirmation: no `git push`, force operations, deploys, or deleting files outside what the task requires. Only commit when asked.
- **Don't reorganize the repository or directory layout** (moving the project, nesting or re-initializing git repos) without being asked.
- **Run the tests** after code changes and report the actual result. If something fails or wasn't verified, say so.
- **Don't start long-running servers** unless the user asks to see the app running, and stop them when done.
- **Keep the user informed** about trade-offs when a request conflicts with the principles above, rather than silently deviating.
