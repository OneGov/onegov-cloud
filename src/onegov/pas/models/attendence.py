from __future__ import annotations

from onegov.parliament.models import Attendence


class PASAttendence(Attendence):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_attendence',
    }

    es_type_name = 'pas_attendence'
    es_public = False
