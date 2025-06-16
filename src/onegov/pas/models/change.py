from __future__ import annotations

from onegov.parliament.models import Change

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.parliament.models import Attendence
    from onegov.parliament.models.change import Action
    from onegov.town6.request import TownRequest


class PASChange(Change):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_change',
    }

    es_type_name = 'pas_change'


@classmethod
def add(
    cls,
    request: TownRequest,
    action: Action,
    attendence: Attendence
) -> Change:
    """ Create a new change and add it to the session. """

    change = cls()
    change.user_id = request.current_username
    change.user_name = (
        request.current_user.title if request.current_user else None
    )
    change.action = action
    change.model = 'attendence'
    change.changes = {
        'id': str(attendence.id),
        'date': attendence.date.isoformat(),
        'duration': attendence.duration,
        'type': attendence.type,
        'parliamentarian': (
            attendence.parliamentarian.title
            if attendence.parliamentarian else ''
        ),
        'parliamentarian_id': str(attendence.parliamentarian_id),
        'commission_id': str(attendence.commission_id or ''),
        'commission': (
            attendence.commission.title
            if attendence.commission else ''
        ),
    }
    request.session.add(change)
    return change
