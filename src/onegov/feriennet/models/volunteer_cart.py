from __future__ import annotations

from itertools import groupby
from onegov.activity import OccasionNeed
from onegov.core.orm.sql import as_selectable_from_path
from onegov.core.utils import module_path
from onegov.feriennet import _
from sedate import overlaps
from sqlalchemy import select


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from datetime import datetime
    from onegov.core.browser_session import BrowserSession
    from onegov.core.types import JSON_ro, RenderData
    from onegov.feriennet.layout import DefaultLayout
    from onegov.feriennet.request import FeriennetRequest
    from sqlalchemy.orm import Query, Session
    from typing import NamedTuple
    from typing import Self
    from uuid import UUID

    class CardItemRow(NamedTuple):
        need_id: UUID
        need_name: str
        start: datetime
        end: datetime
        timezone: str
        activity_title: str
        occasion_id: UUID


class VolunteerCart:
    """ Stores items of the volunteer cart view in the browser session.

    Items stored this way may not overlap with existing items. We want
    to prevent volunteers from signing up for conflicting items.

    """

    def __init__(
        self,
        session: Session,
        browser_session: BrowserSession
    ) -> None:
        self.session = session
        self.browser_session = browser_session

    @classmethod
    def from_request(cls, request: FeriennetRequest) -> Self:
        return cls(request.session, request.browser_session)

    def add(self, need_id: UUID) -> None:
        items: list[UUID] = self.browser_session.get('volunteer_cart', [])
        items.append(need_id)

        self.browser_session.volunteer_cart = items

    def remove(self, need_id: UUID) -> None:
        self.browser_session.volunteer_cart = [
            i for i in self.browser_session.get('volunteer_cart', ())
            if i != need_id
        ]

    def has(self, need_id: UUID) -> bool:
        return need_id in self.ids()

    def ids(self) -> Sequence[UUID]:
        return self.browser_session.get('volunteer_cart', ())

    def clear(self) -> None:
        if 'volunteer_cart' in self.browser_session:
            del self.browser_session.volunteer_cart

    def card_items(
        self,
        need_id: UUID | None = None
    ) -> Query[CardItemRow]:
        stmt = as_selectable_from_path(
            module_path('onegov.feriennet', 'queries/card_items.sql'))

        if need_id is None:
            need_ids = self.browser_session.get('volunteer_cart', ())
        else:
            need_ids = (need_id, )

        query = select(stmt.c).where(stmt.c.need_id.in_(need_ids))
        return self.session.execute(query)

    def overlaps(self, need_id: UUID) -> bool:
        need = self.session.query(OccasionNeed).filter_by(id=need_id).first()

        if not need:
            return False

        for maybe in self.card_items(need_id=need_id):
            for item in self.card_items():
                if overlaps(maybe.start, maybe.end, item.start, item.end):
                    return True

        return False

    def for_frontend(
        self,
        layout: DefaultLayout,
        localize: bool = True
    ) -> Iterator[RenderData]:

        grouped = groupby(self.card_items(), key=lambda i: i.need_id)

        def date(record: CardItemRow) -> str:
            start = record.start
            end = record.end
            if localize:
                start = layout.to_timezone(start, record.timezone)
                end = layout.to_timezone(end, record.timezone)
            return layout.format_datetime_range(start, end)

        def remove(record: CardItemRow) -> str:
            return layout.csrf_protected_url(
                layout.request.link(
                    VolunteerCartAction('remove', record.need_id)))

        for need_id, _records in grouped:
            records = tuple(_records)

            yield {
                'need_id': need_id.hex,
                'occasion_id': records[0].occasion_id.hex,
                'remove': remove(records[0]),
                'activity': records[0].activity_title,
                'dates': [date(r) for r in records],
                'need': records[0].need_name
            }


class VolunteerCartAction:
    """ Represents a single action for the VolunteerCart. """

    def __init__(
        self,
        action: Literal['add', 'remove'],
        target: UUID
    ):
        self.action = action
        self.target = target

    def execute(
        self,
        request: FeriennetRequest,
        cart: VolunteerCart
    ) -> JSON_ro:

        if self.action == 'add':
            if cart.has(self.target):
                return {
                    'success': False,
                    'message': request.translate(_(
                        'This item is already in your list.'
                    ))
                }

            if cart.overlaps(self.target):
                return {
                    'success': False,
                    'message': request.translate(_(
                        'Could not add item. It overlaps with '
                        'another item in your list.'
                    ))
                }

            cart.add(self.target)

        elif self.action == 'remove':
            cart.remove(self.target)

        return {'success': True}
