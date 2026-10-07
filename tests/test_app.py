import re

import pytest

from app import create_app, db
from app.models import Dish, Event


@pytest.fixture
def client():
    app = create_app(
        {
            "TESTING": True,
            "WTF_CSRF_ENABLED": False,
            "SQLALCHEMY_DATABASE_URI": "sqlite://",
        }
    )
    with app.test_client() as c, app.app_context():
        yield c


def make_event(client, **overrides):
    data = {
        "title": "Julbord",
        "date": "2026-12-24",
        "location": "Home",
        "host_name": "Anton",
    }
    data.update(overrides)
    resp = client.post("/", data=data)
    assert resp.status_code == 302
    return re.search(r"/e/([\w-]+)", resp.headers["Location"]).group(1)


def test_create_event_and_view(client):
    token = make_event(client)
    resp = client.get(f"/e/{token}")
    assert resp.status_code == 200
    assert b"Julbord" in resp.data


def test_unknown_event_404(client):
    assert client.get("/e/nope").status_code == 404


def test_add_claim_unclaim_delete(client):
    token = make_event(client)
    client.post(f"/e/{token}/dishes", data={"name": "Ham", "category": "Main"})
    dish = Dish.query.one()
    assert dish.claimed_by is None

    client.post(f"/e/{token}/dishes/{dish.id}/claim", data={"name": "Sara"})
    db.session.expire_all()
    assert db.session.get(Dish, dish.id).claimed_by == "Sara"

    # an already-claimed dish can't be taken over
    client.post(f"/e/{token}/dishes/{dish.id}/claim", data={"name": "Eve"})
    db.session.expire_all()
    assert db.session.get(Dish, dish.id).claimed_by == "Sara"

    client.post(f"/e/{token}/dishes/{dish.id}/unclaim")
    db.session.expire_all()
    assert db.session.get(Dish, dish.id).claimed_by is None

    client.post(f"/e/{token}/dishes/{dish.id}/delete")
    assert Dish.query.count() == 0


def test_htmx_returns_partial(client):
    token = make_event(client)
    resp = client.post(
        f"/e/{token}/dishes",
        data={"name": "Risalamande", "category": "Dessert"},
        headers={"HX-Request": "true"},
    )
    assert resp.status_code == 200
    assert b"Risalamande" in resp.data
    assert b"<html" not in resp.data


def test_dish_scoped_to_event(client):
    t1 = make_event(client)
    t2 = make_event(client)
    client.post(f"/e/{t1}/dishes", data={"name": "Ham", "category": "Main"})
    dish = Dish.query.one()
    assert client.post(f"/e/{t2}/dishes/{dish.id}/delete").status_code == 404


def test_theme_defaults_to_classic(client):
    token = make_event(client)
    assert Event.query.filter_by(token=token).one().theme == "classic"
    assert b'data-event-theme="classic"' in client.get(f"/e/{token}").data


def test_christmas_theme_is_saved_and_applied(client):
    token = make_event(client, theme="christmas")
    assert Event.query.filter_by(token=token).one().theme == "christmas"
    page = client.get(f"/e/{token}").data
    assert b'data-event-theme="christmas"' in page
    assert b'data-theme="light"' in page


def test_invalid_theme_rejected(client):
    resp = client.post(
        "/",
        data={
            "title": "Julbord",
            "date": "2026-12-24",
            "host_name": "Anton",
            "theme": "easter",
        },
    )
    assert resp.status_code == 200
    assert Event.query.count() == 0


def test_halloween_theme_is_saved_and_applied(client):
    token = make_event(client, theme="halloween")
    assert Event.query.filter_by(token=token).one().theme == "halloween"
    page = client.get(f"/e/{token}").data
    assert b'data-event-theme="halloween"' in page
    assert b'data-theme="dark"' in page


def test_sv_date_filter():
    from datetime import date

    from app.format import sv_date

    assert sv_date(date(2026, 12, 24)) == "torsdag 24 december 2026"
    assert sv_date(date(2026, 10, 31)) == "lördag 31 oktober 2026"


def test_pages_are_swedish(client):
    home = client.get("/").get_data(as_text=True)
    assert '<html lang="sv"' in home
    assert "Skapa evenemang" in home
    assert "Halloween" in home and "Klassisk" in home

    token = make_event(client)
    page = client.get(f"/e/{token}").get_data(as_text=True)
    assert "torsdag 24 december 2026" in page
    assert "värd: Anton" in page
    assert "Inga rätter än" in page


def test_category_label_is_swedish_but_stored_key_is_english(client):
    token = make_event(client)
    client.post(f"/e/{token}/dishes", data={"name": "Janssons", "category": "Main"})
    assert Dish.query.one().category == "Main"
    page = client.get(f"/e/{token}").get_data(as_text=True)
    assert "Huvudrätt" in page
    assert ">Main<" not in page


def test_validation_message_is_swedish(client):
    resp = client.post("/", data={"title": "", "date": "2026-12-24", "host_name": "Anton"})
    assert resp.status_code == 200
    assert "Det här fältet är obligatoriskt" in resp.get_data(as_text=True)
    assert Event.query.count() == 0


def test_not_found_page_is_swedish(client):
    resp = client.get("/e/nope")
    assert resp.status_code == 404
    assert "Sidan hittades inte" in resp.get_data(as_text=True)


def _app_with_env(monkeypatch, **env):
    from app import create_app

    for name in ("JULKNYT_SECRET_KEY", "SECRET_KEY"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)
    return create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://"})


def test_warns_when_secret_key_not_set(monkeypatch, caplog):
    _app_with_env(monkeypatch)
    assert "JULKNYT_SECRET_KEY is not set" in caplog.text
    assert "no longer read" not in caplog.text


def test_warning_mentions_old_variable_name(monkeypatch, caplog):
    _app_with_env(monkeypatch, SECRET_KEY="old")
    assert "JULKNYT_SECRET_KEY is not set" in caplog.text
    assert "rename it to JULKNYT_SECRET_KEY" in caplog.text


def test_no_warning_when_secret_key_set(monkeypatch, caplog):
    _app_with_env(monkeypatch, JULKNYT_SECRET_KEY="a-real-secret")
    assert "JULKNYT_SECRET_KEY is not set" not in caplog.text


def test_no_warning_in_debug_or_testing(monkeypatch, caplog):
    from app import create_app

    monkeypatch.delenv("JULKNYT_SECRET_KEY", raising=False)
    create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "DEBUG": True})
    create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "TESTING": True})
    assert "JULKNYT_SECRET_KEY is not set" not in caplog.text
