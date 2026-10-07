# Julknyt 🎄

A small Flask app for planning a Christmas potluck. Create an event, share the link, and guests claim dishes.

Stack: Flask, Jinja2, HTMX, SQLite (Flask-SQLAlchemy), Pico.css.

## Setup and running

### Prerequisites
- Python 3.10 or newer (the project is developed on Python 3.14)
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

Then install the dependencies:

```bash
pip install -r requirements.txt
```

### 3. Configure (optional for local use)
The app reads two environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `JULKNYT_SECRET_KEY` | an insecure development value | Signs sessions and CSRF tokens. **Set a random value anywhere other than your own machine.** |
| `JULKNYT_DATABASE_URL` | `sqlite:///instance/potluck.db` | Database connection string |

When `JULKNYT_SECRET_KEY` is missing and debug mode is off, the app logs a warning at startup. In production, check the log for it.

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
There is nothing to set up. On first start the app creates the `instance/` folder, the SQLite file `instance/potluck.db` and the tables (`instance/` is git-ignored).

- The user running the app needs write access to `instance/`.
- There are no migrations yet. If you change a model, delete `instance/potluck.db` (this deletes all events) or add a migration tool first.

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
Use gunicorn (already in `requirements.txt`) instead of the development server, and set `JULKNYT_SECRET_KEY` first:

```bash
gunicorn -w 2 -b 127.0.0.1:8000 wsgi:app
```

- Put a reverse proxy such as nginx in front of it, or run it as a `systemd` service so it restarts on boot.
- Gunicorn does not run on native Windows. Use the development server there, or WSL or Docker.
- To let guests reach the app from outside your network, use a tunnel such as Cloudflare Tunnel or Tailscale instead of opening router ports.

## Test

```bash
pytest
```
