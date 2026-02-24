from __future__ import annotations

import re
from dateutil.rrule import MO, TU, WE, TH, FR, SA, SU

from onegov.org import _


WEEKDAYS = (
    (MO.weekday, _('Mo')),
    (TU.weekday, _('Tu')),
    (WE.weekday, _('We')),
    (TH.weekday, _('Th')),
    (FR.weekday, _('Fr')),
    (SA.weekday, _('Sa')),
    (SU.weekday, _('Su')),
)

TIMESPANS = (
    (0, _('Disabled')),
    (182, _('6 months')),
    (365, _('1 year')),
    (712, _('2 years')),
    (1068, _('3 years')),
)

KABA_CODE_RE = re.compile(r'^[0-9]{4,6}$')
