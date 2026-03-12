from __future__ import annotations

from dateutil.rrule import rrulestr
from sedate import standardize_date
from datetime import date
from datetime import datetime


def as_rdates(recurrence: str, dtstart: datetime | date | None = None) -> str:
    assert dtstart or 'DTSTART' in recurrence
    if isinstance(dtstart, datetime):
        dates = list(rrulestr(recurrence, dtstart=dtstart.date()))
    else:
        dates = list(rrulestr(recurrence, dtstart=dtstart))
    dates = [standardize_date(date, timezone='UTC') for date in dates]
    return '\n'.join(f"RDATE:{d.strftime('%Y-%m-%dT%H%M%SZ')}" for d in dates)
