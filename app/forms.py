from datetime import date, timedelta

from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional, ValidationError

from .models import (
    CATEGORIES,
    CATEGORY_LABELS,
    DEFAULT_THEME,
    DIETARY_MAX,
    DISH_NAME_MAX,
    LOCATION_MAX,
    NAME_MAX,
    THEMES,
    TITLE_MAX,
)


# How far ahead an event may be planned; mostly a guard against typos like the year 2206.
MAX_DAYS_AHEAD = 365


def _strip(value):
    return (value or "").strip()


class BaseForm(FlaskForm):
    class Meta(FlaskForm.Meta):
        # WTForms' built-in validation messages in Swedish (needs WTF_I18N_ENABLED=False)
        locales = ["sv"]


class EventForm(BaseForm):
    title = StringField(
        "Evenemangets titel",
        validators=[DataRequired(), Length(max=TITLE_MAX)],
        filters=[_strip],
    )
    date = DateField("Datum", validators=[DataRequired()])
    location = StringField(
        "Plats", validators=[Optional(), Length(max=LOCATION_MAX)], filters=[_strip]
    )
    host_name = StringField(
        "Ditt namn", validators=[DataRequired(), Length(max=NAME_MAX)], filters=[_strip]
    )
    theme = SelectField("Tema", choices=THEMES, default=DEFAULT_THEME)

    def validate_date(self, field):
        """Today up to MAX_DAYS_AHEAD days ahead. A past date would be purged right away."""
        today = date.today()
        if field.data < today:
            raise ValidationError("Datumet kan inte ligga i det förflutna.")
        if field.data > today + timedelta(days=MAX_DAYS_AHEAD):
            raise ValidationError("Datumet kan inte vara mer än ett år fram i tiden.")


class DishForm(BaseForm):
    name = StringField(
        "Rätt", validators=[DataRequired(), Length(max=DISH_NAME_MAX)], filters=[_strip]
    )
    category = SelectField("Kategori", choices=[(c, CATEGORY_LABELS[c]) for c in CATEGORIES])
    dietary = StringField(
        "Kostnotering (t.ex. vegansk, glutenfri)",
        validators=[Optional(), Length(max=DIETARY_MAX)],
        filters=[_strip],
    )
    claimed_by = StringField(
        "Ditt namn (lämna tomt för att efterfråga en rätt)",
        validators=[Optional(), Length(max=NAME_MAX)],
        filters=[_strip],
    )


class ClaimForm(BaseForm):
    name = StringField(
        "Ditt namn", validators=[DataRequired(), Length(max=NAME_MAX)], filters=[_strip]
    )
