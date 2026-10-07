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


def _new_token():
    return secrets.token_urlsafe(8)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False, default=_new_token)
    title = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200), default="")
    host_name = db.Column(db.String(80), nullable=False)
    theme = db.Column(db.String(20), nullable=False, default=DEFAULT_THEME)
    dishes = db.relationship(
        "Dish", backref="event", cascade="all, delete-orphan", order_by="Dish.id"
    )


class Dish(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("event.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(20), nullable=False, default="Other")
    dietary = db.Column(db.String(120), default="")
    claimed_by = db.Column(db.String(80), nullable=True)
