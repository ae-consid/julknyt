import os

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFError, CSRFProtect

db = SQLAlchemy()
csrf = CSRFProtect()

DEV_SECRET_KEY = "dev-only-change-me"


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

    if app.config["SECRET_KEY"] == DEV_SECRET_KEY and not (app.debug or app.testing):
        hint = (
            " The old SECRET_KEY variable is no longer read; rename it to JULKNYT_SECRET_KEY."
            if "SECRET_KEY" in os.environ
            else ""
        )
        app.logger.warning(
            "JULKNYT_SECRET_KEY is not set: using the insecure development key, so sessions "
            "and CSRF tokens can be forged. Set JULKNYT_SECRET_KEY before running in "
            "production.%s",
            hint,
        )

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)

    from .format import sv_date
    from .models import CATEGORIES, CATEGORY_LABELS
    from .routes import bp

    app.register_blueprint(bp)
    app.jinja_env.filters["sv_date"] = sv_date
    app.jinja_env.globals["CATEGORIES"] = CATEGORIES
    app.jinja_env.globals["CATEGORY_LABELS"] = CATEGORY_LABELS

    @app.errorhandler(404)
    def not_found(_error):
        return render_template(
            "error.html",
            title="Sidan hittades inte",
            message="Länken verkar vara fel eller så har evenemanget tagits bort.",
        ), 404

    @app.errorhandler(CSRFError)
    def csrf_error(_error):
        return render_template(
            "error.html",
            title="Något gick fel",
            message="Formuläret är ogiltigt eller har gått ut. Ladda om sidan och försök igen.",
        ), 400

    with app.app_context():
        db.create_all()

    return app
