from __future__ import annotations

import isodate
import pytz
import sedate
import transaction

from datetime import time
from libres.db.models import ReservationBlocker
from libres.modules.errors import LibresError
from onegov.core.custom import json
from onegov.core.security import Private
from onegov.org import _, OrgApp
from onegov.org import utils
from onegov.reservation import Allocation
from webob import exc, Response


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.types import JSON_ro
    from onegov.org.request import OrgRequest
    from onegov.reservation import Reservation


def respond_with_success(request: OrgRequest) -> JSON_ro:
    @request.after
    def trigger_calendar_update(response: Response) -> None:
        response.headers.add('X-IC-Trigger', 'oc-reservations-changed')

    return {
        'success': True
    }


def respond_with_error(request: OrgRequest, error: str) -> JSON_ro:
    if type(error) is not str:
        error = request.translate(error)

    message: JSON_ro = {
        'message': error,
        'success': False
    }

    @request.after
    def trigger(response: Response) -> None:
        response.headers.add('X-IC-Trigger', 'oc-reservation-error')
        response.headers.add(
            'X-IC-Trigger-Data',
            json.dumps(message, ensure_ascii=True)
        )

    return message


@OrgApp.json(
    model=Allocation,
    name='add-blocker',
    request_method='POST',
    permission=Private
)
def block_allocation(self: Allocation, request: OrgRequest) -> JSON_ro:
    """ Adds a single blocker to the given allocation. """

    request.assert_valid_csrf_token()

    # the blocker is defined through query parameters
    start_str = request.params.get('start') or f'{self.start:%H:%M}'
    end_str = request.params.get('end') or f'{self.end:%H:%M}'
    if not isinstance(start_str, str) or not isinstance(end_str, str):
        raise exc.HTTPBadRequest()

    reason = request.params.get('reason')
    if reason is not None and not isinstance(reason, str):
        raise exc.HTTPBadRequest()

    whole_day = request.params.get('whole_day') == '1'

    if self.partly_available:
        if self.whole_day and whole_day:
            start_time = time(0, 0)
            end_time = time(23, 59)
        else:
            start_time = sedate.parse_time(start_str)
            end_time = sedate.parse_time(end_str)

        try:
            start, end = sedate.get_date_range(
                self.display_start(),
                start_time,
                end_time,
                raise_non_existent=True
            )
        except pytz.NonExistentTimeError:
            err = request.translate(_(
                'The selected time does not exist on this date due to '
                'the switch from standard time to daylight saving time.'
            ))
            return respond_with_error(request, err)
    else:
        start, end = self.start, self.end

    resource = request.app.libres_resources.by_allocation(self)
    assert resource is not None

    # if the allocation is in the past, disable it...
    if end < sedate.utcnow():
        err = request.translate(_('This date lies in the past'))

        return respond_with_error(request, err)

    # ...otherwise, try to add a blocker
    try:
        resource.scheduler.add_blocker(
            dates=(start, end),
            reason=reason
        )
    except LibresError as e:
        return respond_with_error(request, utils.get_libres_error(e, request))
    else:
        return respond_with_success(request)


@OrgApp.json(
    model=ReservationBlocker,
    request_method='DELETE',
    permission=Private
)
def delete_blocker(self: ReservationBlocker, request: OrgRequest) -> JSON_ro:

    request.assert_valid_csrf_token()

    resource = request.app.libres_resources.by_blocker(self)
    assert resource is not None

    try:
        resource.scheduler.remove_blocker(self.token, self.id)
    except LibresError as e:
        return respond_with_error(request, utils.get_libres_error(e, request))
    else:
        return respond_with_success(request)


@OrgApp.json(
    model=ReservationBlocker,
    name='adjust',
    request_method='POST',
    permission=Private
)
def adjust_blocker(
    self: Reservation,
    request: OrgRequest
) -> JSON_ro:

    request.assert_valid_csrf_token()
    try:
        new_start = isodate.parse_datetime(request.GET['start'])
        new_end = isodate.parse_datetime(request.GET['end'])
    except Exception:
        raise exc.HTTPBadRequest() from None

    token = self.token
    resource = request.app.libres_resources.by_reservation(self)
    assert resource is not None
    blocker_id_str = request.params.get('blocker-id')
    if isinstance(blocker_id_str, str) and blocker_id_str.isdigit():
        blocker_id = int(blocker_id_str)
    else:
        raise exc.HTTPNotFound()

    blocker: ReservationBlocker | None = (
        resource.scheduler.blockers_by_token(token)
        .filter(ReservationBlocker.id == blocker_id)
        .one_or_none()
    )
    if blocker is None or blocker.display_start() < sedate.utcnow():
        return respond_with_error(
            request,
            _('Blocker not adjustable')
        )

    if min(new_start, new_end) < sedate.utcnow():
        return respond_with_error(
            request,
            _('Cannot move blocker into the past')
        )

    savepoint = transaction.savepoint()
    try:
        resource.scheduler.change_blocker(
            token,
            blocker.id,
            new_start,
            new_end,
        )
    except LibresError as e:
        # rollback previous changes
        request.session.flush()
        savepoint.rollback()
        return respond_with_error(request, utils.get_libres_error(e, request))

    return respond_with_success(request)


@OrgApp.json(
    model=ReservationBlocker,
    name='set-reason',
    request_method='POST',
    permission=Private
)
def set_reason(
    self: Reservation,
    request: OrgRequest
) -> JSON_ro:

    request.assert_valid_csrf_token()
    new_reason = request.GET.get('reason') or None
    if new_reason is not None and not isinstance(new_reason, str):
        raise exc.HTTPBadRequest()

    token = self.token
    resource = request.app.libres_resources.by_reservation(self)
    assert resource is not None
    blocker_id_str = request.params.get('blocker-id')
    if isinstance(blocker_id_str, str) and blocker_id_str.isdigit():
        blocker_id = int(blocker_id_str)
    else:
        raise exc.HTTPNotFound()

    blocker: ReservationBlocker | None = (
        resource.scheduler.blockers_by_token(token)
        .filter(ReservationBlocker.id == blocker_id)
        .one_or_none()
    )
    if blocker is None:
        return respond_with_error(
            request,
            _('Blocker no longer exists')
        )

    resource.scheduler.change_blocker_reason(token, new_reason)
    return respond_with_success(request)
