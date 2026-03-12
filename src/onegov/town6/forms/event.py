from __future__ import annotations

from onegov.org.forms import EventForm as OrgEventForm


class EventForm(OrgEventForm):
    on_request_include = ()
