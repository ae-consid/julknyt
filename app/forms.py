from flask_wtf import FlaskForm
from wtforms import DateField, SelectField, StringField
from wtforms.validators import DataRequired, Length, Optional

from .models import CATEGORIES, DEFAULT_THEME, THEMES


class EventForm(FlaskForm):
    title = StringField("Event title", validators=[DataRequired(), Length(max=120)])
    date = DateField("Date", validators=[DataRequired()])
    location = StringField("Location", validators=[Optional(), Length(max=200)])
    host_name = StringField("Your name", validators=[DataRequired(), Length(max=80)])
    theme = SelectField("Theme", choices=THEMES, default=DEFAULT_THEME)


class DishForm(FlaskForm):
    name = StringField("Dish", validators=[DataRequired(), Length(max=120)])
    category = SelectField("Category", choices=[(c, c) for c in CATEGORIES])
    dietary = StringField(
        "Dietary notes (e.g. vegan, gluten-free)", validators=[Optional(), Length(max=120)]
    )
    claimed_by = StringField(
        "Your name (leave empty to request a dish)", validators=[Optional(), Length(max=80)]
    )
