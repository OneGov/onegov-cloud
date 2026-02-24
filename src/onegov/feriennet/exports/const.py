from __future__ import annotations

from onegov.feriennet import _


ACTIVITY_STATES = {
    'accepted': _('Accepted'),
    'archived': _('Archived'),
    'preview': _('Preview'),
    'proposed': _('Proposed'),
    'published': _('Published')
}

FREQUENCIES = {
    'daily': _('Daily'),
    'weekly': _('Weekly'),
    'monthly': _('Monthly'),
    'never': _('Never')
}

SALUTATIONS: dict[str | None, str] = {
    'mr': _('Mr.'),
    'ms': _('Ms.')
}

BOOKING_STATES = {
    'open': _('Open'),
    'accepted': _('Accepted'),
    'cancelled': _('Cancelled'),
    'denied': _('Denied'),
    'blocked': _('Blocked')
}

GENDERS: dict[str | None, str] = {
    'male': _('Boy'),
    'female': _('Girl')
}

ROLES = {
    'admin': _('Administrator'),
    'editor': _('Editor'),
    'member': _('Member'),
}

# Refer to states used in /onegov-cloud/src/onegov/activity/models/volunteer.py
STATES = {
    'open': _('Open'),
    'contacted': _('Contacted'),
    'confirmed': _('Confirmed')
}
