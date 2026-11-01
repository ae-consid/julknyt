from datetime import date, timedelta

from . import db
from .models import Event

# Events are removed this many days after their date.
RETENTION_DAYS = 7


def delete_expired_events(today=None):
    """Delete events whose date is RETENTION_DAYS or more days past; return how many.

    Events are deleted one by one through the ORM so the cascade removes their dishes too (a
    bulk query delete would skip it, and SQLite doesn't enforce foreign keys by default).
    """
    cutoff = (today or date.today()) - timedelta(days=RETENTION_DAYS)
    expired = Event.query.filter(Event.date <= cutoff).all()
    for event in expired:
        db.session.delete(event)
    db.session.commit()
    return len(expired)
