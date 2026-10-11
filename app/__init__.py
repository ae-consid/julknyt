import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()

DEV_SECRET_KEY = "dev-only-change-me"


def _require_secret_key(app):
    """Refuse to run with the public development key outside debug mode and tests."""
    if app.config["SECRET_KEY"] != DEV_SECRET_KEY or app.debug or app.testing:
        return
    raise RuntimeError(
        "JULKNYT_SECRET_KEY is not set. Without it sessions and CSRF tokens can be forged, "
        "so the app will not start outside debug mode. Set JULKNYT_SECRET_KEY to a random "
        "value (see the README). The old SECRET_KEY variable is no longer read."
    )


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
        SECRET_KEY=os.environ.get("JULKNYT_SECRET_KEY", DEV_SECRET_KEY),
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

    from .format import sv_date
    from .models import CATEGORIES, CATEGORY_LABELS, THEME_PICO_MODES
    from .routes import bp

    app.register_blueprint(bp)
    app.jinja_env.filters["sv_date"] = sv_date
    app.jinja_env.globals["CATEGORIES"] = CATEGORIES
    app.jinja_env.globals["CATEGORY_LABELS"] = CATEGORY_LABELS
    app.jinja_env.globals["THEME_PICO_MODES"] = THEME_PICO_MODES

    _register_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app
