# Julknyt 🎄

A small web app for planning a Christmas potluck, so nobody ends up bringing the same dish.

**Live:** <https://aeconsid.pythonanywhere.com/>

## What it does

A host creates an event with a title, date, location and theme, and shares its link. Guests open the link, see which dishes are planned, and add, claim, unclaim or remove dishes. There are no accounts: the link is the access, and guests identify themselves by typing a name. The interface is in Swedish.

## Getting started

### Requirements

- Python 3.11 or newer (developed and tested on Python 3.14)
- git
- No external services or API keys

### Installation

```bash
git clone https://github.com/ae-consid/julknyt.git
cd julknyt
python -m venv .venv
```

Activate the virtual environment (see [Virtual environment](#virtual-environment) for every shell), then install the dependencies:

```bash
pip install -r requirements-dev.txt
```

`requirements-dev.txt` includes pytest. To run the app only, `pip install -r requirements.txt` is enough.

### Configuration

The app is configured with environment variables. There is no `.env` file and no `.env.example`.

| Variable | Default | Purpose |
|---|---|---|
| `JULKNYT_SECRET_KEY` | none (a random key per run in debug mode) | Signs sessions and CSRF tokens. At least 32 characters. **Set a random value anywhere other than your own machine.** |
| `JULKNYT_DATABASE_URL` | `sqlite:///instance/potluck.db` | Database connection string |

Outside debug mode (`--debug`) and the tests, the app **refuses to start** without `JULKNYT_SECRET_KEY`. A key shorter than 32 characters is rejected in every mode. For local development, `flask --app wsgi run --debug` works without it: the app makes up a random key for that run, so open pages need a reload after the server restarts.

Generate a key and set it for the current terminal session:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

```powershell
$env:JULKNYT_SECRET_KEY = "paste-the-generated-key-here"
```

```bash
export JULKNYT_SECRET_KEY="paste-the-generated-key-here"
```

### Run the project

Create the database once (and again after every update that adds a migration), then start the development server:

```bash
flask --app wsgi db upgrade
flask --app wsgi run --debug
```

Open <http://127.0.0.1:5000>. Stop the server with `Ctrl+C`. If port 5000 is already in use, add `--port 5001`. More on the database under [Database](#database).

## Architecture

Julknyt is a server-rendered Flask app. `create_app` in `app/__init__.py` builds the application (configuration, error handlers, security headers, the `purge-events` command), and a single blueprint in `app/routes.py` holds all the routes. Routes are thin: they validate input with Flask-WTF forms (`app/forms.py`), call the models (`app/models.py`) and render Jinja2 templates. Every dish is looked up through the event identified by the share token in the URL, never by id alone. Interactivity comes from HTMX: HTMX requests get only the `_dishes.html` partial, while plain form posts redirect, so the app also works without JavaScript.

```
julknyt/
├── app/
│   ├── __init__.py    # create_app, error handlers, security headers, CLI command
│   ├── routes.py      # the blueprint: index, event page, add/claim/unclaim/delete dish
│   ├── models.py      # Event and Dish, categories, themes and length limits
│   ├── forms.py       # WTForms forms and validation (Swedish messages)
│   ├── cleanup.py     # deletes events 7+ days past their date
│   ├── format.py      # Swedish date formatting (the sv_date filter)
│   ├── templates/     # Jinja2 templates; _dishes.html is the partial HTMX swaps
│   └── static/        # style.css
├── migrations/        # Flask-Migrate (Alembic) schema migrations
├── tests/             # pytest tests (in-memory SQLite, CSRF disabled)
├── wsgi.py            # entry point for gunicorn and the flask command
├── requirements.txt       # runtime dependencies
└── requirements-dev.txt   # adds pytest
```

## Tech stack

| Component | Choice | Reason |
|---|---|---|
| Backend | Flask 3 | Small and simple for an app with a handful of routes; the application factory keeps testing easy |
| Templates | Jinja2 (server-rendered) | Returns HTML rather than JSON, so there is no separate frontend to build or host |
| Interactivity | HTMX | Updates the dish list without a JavaScript framework or build step, and degrades to plain form posts |
| Database | SQLite via Flask-SQLAlchemy | No infrastructure to run, enough for small groups |
| Migrations | Flask-Migrate | Schema changes are versioned and reviewable |
| Forms and CSRF | Flask-WTF | Input validation and CSRF protection in one place |
| Styling | Pico.css (CDN) | Clean default look with almost no custom CSS |
| Tests | pytest | Simple and fast |
| Production server | gunicorn | Standard WSGI server for Linux hosts |

## Limitations

- **The link is the only access control.** Anyone who has it can change the list, including unclaiming and removing other guests' dishes. Claims are tied to a typed name, not to an identity. Share the link only with people you trust.
- **Small scale.** SQLite and the lack of rate limiting suit a handful of people, not a public service. An event holds at most 50 dishes.
- **Events are temporary.** An event is deleted 7 days after its date, but only if `purge-events` is run on a schedule (see [Data retention](#data-retention)). The date must be today or up to a year ahead.
- **Swedish only.** There is no language switcher.
- **Needs internet access for the browser.** Pico.css and HTMX are loaded from CDNs. Without them the page loses its styling and the live updates, though the forms still work.
- **No Windows production server.** gunicorn does not run on native Windows.

## Built with

Claude Code (agentic development) as part of the course Next-Generation Software Development with AI.

---

# Operations and reference

## Virtual environment

Create it once with `python -m venv .venv`, then activate it:

| Shell | Command |
|---|---|
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows cmd | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

If PowerShell blocks the activation script, allow it for the current window only:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

Both requirements files pin exact versions of the direct dependencies; they were tested on Python 3.14.

## Database

The schema is managed with Flask-Migrate (Alembic). Create the database (the `instance/` folder and the SQLite file `instance/potluck.db`, which is git-ignored) by running the migrations, and again after every update that adds a migration:

```bash
flask --app wsgi db upgrade
```

The command needs `JULKNYT_SECRET_KEY`, like the app itself; for local development `flask --app wsgi --debug db upgrade` works without it.

- The user running the app needs write access to `instance/`.
- **Already have a database from before migrations were added?** It has the same tables, so mark it as up to date instead of upgrading: `flask --app wsgi db stamp head` (once).
- **Changing a model:** edit `app/models.py`, then `flask --app wsgi db migrate -m "what changed"`, read the new file in `migrations/versions/`, commit it, and run `flask --app wsgi db upgrade`. A test fails if a model and the migrations disagree.

## Data retention

Events are removed 7 days after their date. The app does not do this itself; run the command daily from a scheduler (for example the Tasks tab on PythonAnywhere, or cron):

```bash
flask --app wsgi purge-events
```

It deletes the events together with their dishes. If the database cannot be written, it exits with an error so the scheduler can mark the run as failed.

## Running in production (Linux)

Use gunicorn (already in `requirements.txt`) instead of the development server. Set `JULKNYT_SECRET_KEY` first and run `flask --app wsgi db upgrade` on every deploy:

```bash
gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app
```

- Put a reverse proxy such as nginx in front of it, or run it as a `systemd` service so it restarts on boot.
- Gunicorn does not run on native Windows. Use the development server there, or WSL or Docker.
- **Logs contain the event links.** The event link (`/e/<token>`) is the only credential, so anyone who can read an access log can open and change every event in it. Gunicorn's access log is off by default, so don't enable it (`--access-logfile`). In nginx, mask the token in the log format (`$request` and `$request_uri` contain it):

  ```nginx
  map $uri $logged_uri { ~^/e/ "/e/[token]"; default $uri; }
  log_format masked '$remote_addr "$request_method $logged_uri" $status';
  access_log /var/log/nginx/julknyt.log masked;
  ```

  Also restrict read access to the log files and rotate them. The development server prints every URL to the terminal, so don't share its output.
- To let guests reach the app from outside your network, use a tunnel such as Cloudflare Tunnel or Tailscale instead of opening router ports.

## Tests

Needs the development dependencies (`requirements-dev.txt`):

```bash
pytest
```
