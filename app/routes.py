from flask import Blueprint, abort, make_response, redirect, render_template, request, url_for

from . import db
from .forms import ClaimForm, DishForm, EventForm
from .models import Dish, Event

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


def _is_htmx():
    return bool(request.headers.get("HX-Request"))


def _event_page(event, form=None, claim_errors=None):
    # formdata=None: don't fill the add-dish form from the POST that got us here
    form = form or DishForm(formdata=None)
    return render_template(
        "event.html",
        event=event,
        form=form,
        claim_errors=claim_errors,
        theme=event.theme,
    )


def _dish_response(event, claim_errors=None, fresh_form=False):
    """HTMX requests get the dish list partial; plain form posts get a redirect.

    claim_errors ({dish_id: [messages]}) are shown next to that dish; a plain post then
    re-renders the page instead of redirecting. fresh_form also swaps in an empty add-dish
    form (out of band), replacing the one the user just filled in.
    """
    if _is_htmx():
        # Reload event.dishes so the partial shows the list as it is after the change
        # that was just committed.
        db.session.refresh(event)
        html = render_template("_dishes.html", event=event, claim_errors=claim_errors)
        if fresh_form:
            html += render_template(
                "_dish_form.html", event=event, form=DishForm(formdata=None), oob=True
            )
        return html
    if claim_errors:
        return _event_page(event, claim_errors=claim_errors)
    return redirect(url_for("main.event", token=event.token))


@bp.route("/", methods=["GET", "POST"])
def index():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            title=form.title.data,
            date=form.date.data,
            location=form.location.data,
            host_name=form.host_name.data,
            theme=form.theme.data,
        )
        db.session.add(event)
        db.session.commit()
        return redirect(url_for("main.event", token=event.token))
    return render_template("index.html", form=form, theme=form.theme.data)


# endpoint="event" keeps url_for("main.event") working; the function name would
# otherwise clash with the local `event` variables in the routes below.
@bp.get("/e/<token>", endpoint="event")
def show_event(token):
    return _event_page(_get_event(token))


@bp.post("/e/<token>/dishes")
def add_dish(token):
    event = _get_event(token)
    form = DishForm()
    if not form.validate_on_submit():
        if _is_htmx():
            # Swap only the form (with its errors); the dish list stays as it is.
            response = make_response(
                render_template("_dish_form.html", event=event, form=form)
            )
            response.headers["HX-Retarget"] = "#add-dish"
            response.headers["HX-Reswap"] = "outerHTML"
            return response
        return _event_page(event, form=form)
    db.session.add(
        Dish(
            event=event,
            name=form.name.data,
            category=form.category.data,
            dietary=form.dietary.data,
            claimed_by=form.claimed_by.data or None,
        )
    )
    db.session.commit()
    return _dish_response(event, fresh_form=True)


@bp.post("/e/<token>/dishes/<int:dish_id>/claim")
def claim(token, dish_id):
    event, dish = _get_dish(token, dish_id)
    form = ClaimForm()
    if not form.validate_on_submit():
        return _dish_response(event, claim_errors={dish.id: form.name.errors})
    if dish.claimed_by is None:
        dish.claimed_by = form.name.data
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
