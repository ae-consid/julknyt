from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional

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


class BaseForm(FlaskForm):
    class Meta(FlaskForm.Meta):
        # WTForms' built-in validation messages in Swedish (needs WTF_I18N_ENABLED=False)
        locales = ["sv"]


class EventForm(BaseForm):
    title = StringField("Evenemangets titel", validators=[DataRequired(), Length(max=TITLE_MAX)])
    date = DateField("Datum", validators=[DataRequired()])
    location = StringField("Plats", validators=[Optional(), Length(max=LOCATION_MAX)])
    host_name = StringField("Ditt namn", validators=[DataRequired(), Length(max=NAME_MAX)])
    theme = SelectField("Tema", choices=THEMES, default=DEFAULT_THEME)


class DishForm(BaseForm):
    name = StringField("Rätt", validators=[DataRequired(), Length(max=DISH_NAME_MAX)])
    category = SelectField("Kategori", choices=[(c, CATEGORY_LABELS[c]) for c in CATEGORIES])
    dietary = StringField(
        "Kostnotering (t.ex. vegansk, glutenfri)", validators=[Optional(), Length(max=DIETARY_MAX)]
    )
    claimed_by = StringField(
        "Ditt namn (lämna tomt för att efterfråga en rätt)",
        validators=[Optional(), Length(max=NAME_MAX)],
    )
