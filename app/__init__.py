import os
import secrets

from flask import Flask, render_template
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect

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


def _error_page(title, message, status):
    return render_template("error.html", title=title, message=message), status


def _register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_error):
        return _error_page(
            "Sidan hittades inte",
            "Länken verkar vara fel eller så har evenemanget tagits bort.",
            404,
        )

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        return _error_page(
            "Något gick fel",
            "Formuläret är ogiltigt eller har gått ut. Ladda om sidan och försök igen.",
            400,
        )


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

    return app
