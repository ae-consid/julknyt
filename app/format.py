WEEKDAYS = ["måndag", "tisdag", "onsdag", "torsdag", "fredag", "lördag", "söndag"]
MONTHS = [
    "januari", "februari", "mars", "april", "maj", "juni",
    "juli", "augusti", "september", "oktober", "november", "december",
]


def sv_date(value):
    """Format a date in Swedish, e.g. 'torsdag 24 december 2026' (strftime is English-only)."""
    return f"{WEEKDAYS[value.weekday()]} {value.day} {MONTHS[value.month - 1]} {value.year}"
