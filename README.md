# Julknyt 🎄

A small Flask app for planning a Christmas potluck. Create an event, share the link, and guests claim dishes.

Stack: Flask, Jinja2, HTMX, SQLite (Flask-SQLAlchemy, Flask-Migrate), Pico.css.

## Setup and running

### Prerequisites
- Python 3.11 or newer (developed and tested on Python 3.14; the latest SQLAlchemy needs 3.11)
- git

### 1. Get the code
```bash
git clone https://github.com/ae-consid/julknyt.git
cd julknyt
```

### 2. Create a virtual environment and install dependencies
```bash
python -m venv .venv
```

Activate it:

| Shell | Command |
|---|---|
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows cmd | `.venv\Scripts\activate.bat` |
| macOS / Linux | `source .venv/bin/activate` |

If PowerShell blocks the activation script, allow it for the current window only:

```powershell
Set-ExecutionPolicy -Scope Process RemoteSigned
```

Then install the dependencies. For development (includes pytest):

```bash
pip install -r requirements-dev.txt
```

For running the app only, `pip install -r requirements.txt` is enough. Both files pin exact versions of the direct dependencies; they were tested on Python 3.14.

### 3. Configure
The app reads two environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `JULKNYT_SECRET_KEY` | an insecure development value | Signs sessions and CSRF tokens. **Set a random value anywhere other than your own machine.** |
| `JULKNYT_DATABASE_URL` | `sqlite:///instance/potluck.db` | Database connection string |

Outside debug mode (`--debug`) and the tests, the app **refuses to start** without `JULKNYT_SECRET_KEY`, because sessions and CSRF tokens could be forged with the built-in development key. For local development, `flask --app wsgi run --debug` works without it.

Generate a key:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Set it for the current terminal session:

```powershell
$env:JULKNYT_SECRET_KEY = "paste-the-generated-key-here"
```

```bash
export JULKNYT_SECRET_KEY="paste-the-generated-key-here"
```

### 4. Database
The schema is managed with Flask-Migrate (Alembic). Create the database (the `instance/` folder and the SQLite file `instance/potluck.db`, which is git-ignored) by running the migrations once, and again after every update that adds a migration:

```bash
flask --app wsgi db upgrade
```

The command needs `JULKNYT_SECRET_KEY` (step 3), like the app itself; for local development `flask --app wsgi --debug db upgrade` works without it.

- The user running the app needs write access to `instance/`.
- **Already have a database from before migrations were added?** It has the same tables, so mark it as up to date instead of upgrading: `flask --app wsgi db stamp head` (once).
- **Changing a model:** edit `app/models.py`, then `flask --app wsgi db migrate -m "what changed"`, read the new file in `migrations/versions/`, commit it, and run `flask --app wsgi db upgrade`. A test fails if a model and the migrations disagree.

### 5. Run the development server
```bash
flask --app wsgi run --debug
```

Open <http://127.0.0.1:5000>. Stop the server with `Ctrl+C`. If port 5000 is already in use, add `--port 5001`.

### 6. Use the app
1. On the start page, enter a title, date, location and your name, and pick a theme (Classic, Christmas or Halloween).
2. Share the event page's link with your guests. Anyone with the link can open it.
3. Guests add dishes, claim them with their name, or unclaim and remove them.

The user interface is in Swedish.

### Running in production (Linux)
Use gunicorn (already in `requirements.txt`) instead of the development server. Set `JULKNYT_SECRET_KEY` first and run `flask --app wsgi db upgrade` on every deploy:

```bash
gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app
```

- Put a reverse proxy such as nginx in front of it, or run it as a `systemd` service so it restarts on boot.
- Gunicorn does not run on native Windows. Use the development server there, or WSL or Docker.
- To let guests reach the app from outside your network, use a tunnel such as Cloudflare Tunnel or Tailscale instead of opening router ports.

## Test

Needs the development dependencies (`requirements-dev.txt`):

```bash
pytest
```
