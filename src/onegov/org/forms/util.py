from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

from onegov.org import _


WEEKDAYS = (
    (MO.weekday, _("Mo")),
    (TU.weekday, _("Tu")),
    (WE.weekday, _("We")),
    (TH.weekday, _("Th")),
    (FR.weekday, _("Fr")),
    (SA.weekday, _("Sa")),
    (SU.weekday, _("Su")),
)
