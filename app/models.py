import secrets

from . import db

# Stored values stay English keys; the second element is the Swedish label shown in the UI.
CATEGORIES = ["Starter", "Main", "Side", "Dessert", "Drink", "Other"]
CATEGORY_LABELS = {
    "Starter": "Förrätt",
    "Main": "Huvudrätt",
    "Side": "Tillbehör",
    "Dessert": "Efterrätt",
    "Drink": "Dryck",
    "Other": "Övrigt",
}
THEMES = [
    ("classic", "Klassisk"),
    ("christmas", "Jul 🎄"),
    ("halloween", "Halloween 🎃"),
]
DEFAULT_THEME = "classic"

# Max lengths shared by the DB columns below and the form validators in forms.py.
TITLE_MAX = 120
LOCATION_MAX = 200
NAME_MAX = 80  # host_name and claimed_by
DISH_NAME_MAX = 120
DIETARY_MAX = 120
CATEGORY_MAX = 20
THEME_MAX = 20


def _new_token():
    return secrets.token_urlsafe(8)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False, default=_new_token)
    title = db.Column(db.String(TITLE_MAX), nullable=False)
    date = db.Column(db.Date, nullable=False)
    # An empty location is stored as "" (not None).
    location = db.Column(db.String(LOCATION_MAX), default="")
    host_name = db.Column(db.String(NAME_MAX), nullable=False)
    theme = db.Column(db.String(THEME_MAX), nullable=False, default=DEFAULT_THEME)
    dishes = db.relationship(
        "Dish", backref="event", cascade="all, delete-orphan", order_by="Dish.id"
    )


class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    name = db.Column(db.String(DISH_NAME_MAX), nullable=False)
    category = db.Column(db.String(CATEGORY_MAX), nullable=False, default="Other")
    # An empty dietary note is stored as ""; claimed_by is None while the dish is unclaimed.
    dietary = db.Column(db.String(DIETARY_MAX), default="")
    claimed_by = db.Column(db.String(NAME_MAX), nullable=True)
