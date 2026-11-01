import os
import secrets

import click
from flask import Flask, make_response, render_template, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect
from sqlalchemy.exc import SQLAlchemyError

db = SQLAlchemy()
csrf = CSRFProtect()
migrate = Migrate()

MIN_SECRET_KEY_LENGTH = 32


def _require_secret_key(app):
    """Make sure the app has a strong secret key.

    Outside debug mode and tests the key must come from JULKNYT_SECRET_KEY. In debug mode and
    tests a random key is generated for this process instead, so there is no well-known key
    that could end up in production by mistake (sessions then reset when the server restarts).
    """
    key = app.config.get("SECRET_KEY")
    if key is None:
        if not (app.debug or app.testing):
            raise RuntimeError(
                "JULKNYT_SECRET_KEY is not set. Without it sessions and CSRF tokens can be "
                "forged, so the app will not start outside debug mode. Set JULKNYT_SECRET_KEY "
                "to a random value (see the README). The old SECRET_KEY variable is no longer "
                "read."
            )
        app.config["SECRET_KEY"] = secrets.token_hex(32)
    elif len(key) < MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            f"JULKNYT_SECRET_KEY is too short: it must be at least {MIN_SECRET_KEY_LENGTH} "
            "characters. Generate one as described in the README."
        )


def _add_security_headers(app):
    @app.after_request
    def set_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        # The event link is the only credential, so keep it out of Referer headers sent to the CDNs.
        response.headers["Referrer-Policy"] = "same-origin"
        # Stops the page being framed (clickjacking). X-Frame-Options is for older browsers.
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
        )
        return response


def _error_page(title, message, status, htmx_message=None):
    """Full error page, or for HTMX requests a short message swapped into #htmx-error."""
    if request.headers.get("HX-Request"):
        response = make_response(
            render_template("_htmx_error.html", message=htmx_message or message), status
        )
        response.headers["HX-Retarget"] = "#htmx-error"
        response.headers["HX-Reswap"] = "innerHTML"
        return response
    return render_template("error.html", title=title, message=message), status


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_error):
        return _error_page(
            "Sidan hittades inte",
            "Länken verkar vara fel eller så har evenemanget tagits bort.",
            404,
            htmx_message="Det du försökte ändra finns inte längre. Ladda om sidan.",
        )

    @app.errorhandler(405)
    def method_not_allowed(error):
        response = make_response(
            _error_page(
                "Metoden stöds inte",
                "Den här sidan kan inte öppnas på det sättet. Gå till startsidan och försök igen.",
                405,
            )
        )
        # Werkzeug's own 405 response carries Allow; keep it, as HTTP requires.
        response.headers["Allow"] = ", ".join(error.valid_methods or [])
        return response

    # CSRFError is a BadRequest too, but Flask picks the more specific handler below.
    @app.errorhandler(400)
    def bad_request(_error):
        return _error_page(
            "Ogiltig förfrågan",
            "Förfrågan gick inte att tolka. Ladda om sidan och försök igen.",
            400,
        )

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        return _error_page(
            "Något gick fel",
            "Formuläret är ogiltigt eller har gått ut. Ladda om sidan och försök igen.",
            400,
        )

    @app.errorhandler(503)
    def database_busy(_error):
        return _error_page(
            "Databasen är upptagen",
            "Ändringen sparades inte. Försök igen om en stund.",
            503,
        )

    # Any database failure during a request (a locked SQLite file, a missing table, a failed
    # commit) answers 503. Flask only logs exceptions that reach the 500 handler, so log here.
    @app.errorhandler(SQLAlchemyError)
    def database_error(error):
        db.session.rollback()
        app.logger.error("Database error", exc_info=error)
        return database_busy(error)

    # Flask has already logged the exception by the time this runs.
    @app.errorhandler(500)
    def server_error(_error):
        return _error_page(
            "Något gick fel",
            "Något gick fel hos oss. Försök igen om en stund.",
            500,
        )


def _register_cli(app):
    @app.cli.command("purge-events")
    def purge_events():
        """Delete events that are 7 or more days past their date."""
        from .cleanup import delete_expired_events

        try:
            count = delete_expired_events()
        except SQLAlchemyError as error:
            app.logger.exception("purge-events failed")
            # Exit code 1 lets the scheduler mark the run as failed.
            reason = getattr(error, "orig", None) or error
            raise click.ClickException(f"Kunde inte ta bort gamla evenemang: {reason}")
        click.echo(f"Tog bort {count} gamla evenemang.")


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("JULKNYT_SECRET_KEY"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "JULKNYT_DATABASE_URL", f"sqlite:///{os.path.join(app.instance_path, 'potluck.db')}"
        ),
        # Let WTForms use its own bundled catalogs (see BaseForm.Meta.locales in forms.py)
        WTF_I18N_ENABLED=False,
    )
    if test_config:
        app.config.update(test_config)

    _require_secret_key(app)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    # The schema is managed by migrations (flask --app wsgi db upgrade), not create_all().
    migrations_dir = os.path.join(os.path.dirname(app.root_path), "migrations")
    migrate.init_app(app, db, directory=migrations_dir)

    from .format import sv_date
    from .models import CATEGORIES, CATEGORY_LABELS, NAME_MAX, THEME_PICO_MODES
    from .routes import bp

    app.register_blueprint(bp)
    app.jinja_env.filters["sv_date"] = sv_date
    app.jinja_env.globals["CATEGORIES"] = CATEGORIES
    app.jinja_env.globals["CATEGORY_LABELS"] = CATEGORY_LABELS
    app.jinja_env.globals["NAME_MAX"] = NAME_MAX
    app.jinja_env.globals["THEME_PICO_MODES"] = THEME_PICO_MODES

    _register_error_handlers(app)
    _add_security_headers(app)
    _register_cli(app)

    return app
