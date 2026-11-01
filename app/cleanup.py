from datetime import date, timedelta

from sqlalchemy.exc import SQLAlchemyError

from . import db
from .models import Event

# Events are removed this many days after their date.
RETENTION_DAYS = 7


def delete_expired_events(today=None):
    """Delete events whose date is RETENTION_DAYS or more days past; return how many.

    Events are deleted one by one through the ORM so the cascade removes their dishes too (a
    bulk query delete would skip it, and SQLite doesn't enforce foreign keys by default).
    If the commit fails the session is rolled back and the error is raised again.
    """
    cutoff = (today or date.today()) - timedelta(days=RETENTION_DAYS)
    expired = Event.query.filter(Event.date <= cutoff).all()
    for event in expired:
        db.session.delete(event)
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise
    return len(expired)
