from flask import Blueprint, abort, redirect, render_template, request, url_for

from . import db
from .forms import DishForm, EventForm
from .models import CATEGORIES, Dish, Event

bp = Blueprint("main", __name__)


def _get_event(token):
    event = Event.query.filter_by(token=token).first()
    if event is None:
        abort(404)
    return event


def _get_dish(token, dish_id):
    event = _get_event(token)
    dish = db.session.get(Dish, dish_id)
    if dish is None or dish.event_id != event.id:
        abort(404)
    return event, dish


@bp.route("/", methods=["GET", "POST"])
def index():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data.strip(),
            date=form.date.data,
            location=(form.location.data or "").strip(),
            host_name=form.host_name.data.strip(),
            theme=form.theme.data,
        )
        db.session.add(event)
        db.session.commit()
        return redirect(url_for("main.event", token=event.token))
    return render_template("index.html", form=form, theme=form.theme.data)


@bp.get("/e/<token>")
def event(token):
    event = _get_event(token)
    return render_template(
        "event.html",
        event=event,
        form=DishForm(),
        categories=CATEGORIES,
        theme=event.theme,
    )


@bp.post("/e/<token>/dishes")
def add_dish(token):
    event = _get_event(token)
    form = DishForm()
    if form.validate_on_submit():
        db.session.add(
            Dish(
                event=event,
                name=form.name.data.strip(),
                category=form.category.data,
                dietary=(form.dietary.data or "").strip(),
                claimed_by=(form.claimed_by.data or "").strip() or None,
            )
        )
        db.session.commit()
    return _dish_response(event)


@bp.post("/e/<token>/dishes/<int:dish_id>/claim")
def claim(token, dish_id):
    event, dish = _get_dish(token, dish_id)
    name = request.form.get("name", "").strip()[:80]
    if name and dish.claimed_by is None:
        dish.claimed_by = name
        db.session.commit()
    return _dish_response(event)


@bp.post("/e/<token>/dishes/<int:dish_id>/unclaim")
def unclaim(token, dish_id):
    event, dish = _get_dish(token, dish_id)
    dish.claimed_by = None
    db.session.commit()
    return _dish_response(event)


@bp.post("/e/<token>/dishes/<int:dish_id>/delete")
def delete(token, dish_id):
    event, dish = _get_dish(token, dish_id)
    db.session.delete(dish)
    db.session.commit()
    return _dish_response(event)


def _dish_response(event):
    """HTMX requests get the dish list partial; plain form posts get a redirect."""
    if request.headers.get("HX-Request"):
        db.session.refresh(event)
        return render_template("_dishes.html", event=event, categories=CATEGORIES)
    return redirect(url_for("main.event", token=event.token))
