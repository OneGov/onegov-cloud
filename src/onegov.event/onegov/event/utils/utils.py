from dateutil.rrule import rrulestr
from sedate import standardize_date


def as_rdates(recurrence):
    return '\n'.join(
        f"RDATE:{d.strftime('%Y-%m-%dT%H%M%SZ')}" for d in (
            standardize_date(date, timezone='UTC')
            for date in rrulestr(recurrence)
        )
    )
