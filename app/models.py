import secrets

from . import db

CATEGORIES = ["Starter", "Main", "Side", "Dessert", "Drink", "Other"]


def _new_token():
    return secrets.token_urlsafe(8)


class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(32), unique=True, nullable=False, default=_new_token)
    title = db.Column(db.String(120), nullable=False)
    date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(200), default="")
    host_name = db.Column(db.String(80), nullable=False)
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
