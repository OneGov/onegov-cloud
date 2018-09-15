import logging
log = logging.getLogger('onegov.event')  # noqa
log.addHandler(logging.NullHandler())  # noqa

from onegov.event.models import Event, Occurrence
from onegov.event.collections import EventCollection, OccurrenceCollection


__all__ = [
    'Event',
    'EventCollection',
    'log',
    'Occurrence',
    'OccurrenceCollection',
]
