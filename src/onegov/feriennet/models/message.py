from __future__ import annotations

from onegov.activity import BookingPeriod
from onegov.chat import Message
from onegov.org.models.message import TicketMessageMixin


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.activity.models import BookingPeriodMeta
    from onegov.feriennet.request import FeriennetRequest
    from onegov.ticket import Ticket
    from typing import Self


class PeriodMessage(Message):

    __mapper_args__ = {
        'polymorphic_identity': 'period'
    }

    def link(self, request: FeriennetRequest) -> str:
        return request.class_link(BookingPeriod, {'id': self.channel_id})

    @classmethod
    def create(
        cls,
        period: BookingPeriod | BookingPeriodMeta,
        request: FeriennetRequest,
        action: str
    ) -> Self:
        assert request.current_username, 'reserved for logged-in users'

        return cls.bound_messages(request.session).add(
            channel_id=period.id.hex,
            owner=request.current_username,
            meta={
                'title': period.title,
                'action': action
            }
        )


class ActivityMessage(Message, TicketMessageMixin):

    __mapper_args__ = {
        'polymorphic_identity': 'activity'
    }

    @classmethod
    def create(  # type:ignore[override]
        cls,
        ticket: Ticket,
        request: FeriennetRequest,
        action: str,
        **extra_meta: Any
    ) -> Self:
        # FIXME: This used to pass a scalar extra_meta=extra_meta
        #        so it's possible there are some messages where the
        #        extra_meta is now nested inside .meta['extra_meta']
        #        if so we should fix this with a migration
        return super().create(ticket, request, action=action, **extra_meta)
