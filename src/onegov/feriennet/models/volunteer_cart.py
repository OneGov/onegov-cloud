from itertools import groupby
from onegov.activity import OccasionNeed
from onegov.core.orm.sql import as_selectable_from_path
from onegov.core.utils import module_path
from onegov.feriennet import _
from sedate import overlaps
from sqlalchemy import select


class VolunteerCart(object):
    """ Stores items of the volunteer cart view in the browser session.

    Items stored this way may not overlap with existing items. We want
    to prevent volunteers from signing up for conflicting items.

    """

    def __init__(self, session, browser_session):
        self.session = session
        self.browser_session = browser_session

    @classmethod
    def from_request(cls, request):
        return cls(request.session, request.browser_session)

    def add(self, need_id):
        items = self.browser_session.get('volunteer_cart', [])
        items.append(need_id)

        self.browser_session.volunteer_cart = items

    def remove(self, need_id):
        self.browser_session.volunteer_cart = [
            i for i in self.browser_session.get('volunteer_cart', ())
            if i != need_id
        ]

    def has(self, need_id):
        return need_id in self.ids()

    def ids(self):
        return self.browser_session.get('volunteer_cart', ())

    def clear(self):
        if 'volunteer_cart' in self.browser_session:
            del self.browser_session.volunteer_cart

    def card_items(self, need_id=None):
        stmt = as_selectable_from_path(
            module_path('onegov.feriennet', 'queries/card_items.sql'))

        if need_id is None:
            need_ids = self.browser_session.get('volunteer_cart', ())
        else:
            need_ids = (need_id, )

        query = select(stmt.c).where(stmt.c.need_id.in_(need_ids))
        return self.session.execute(query)

    def overlaps(self, need_id):
        need = self.session.query(OccasionNeed).filter_by(id=need_id).first()

        if not need:
            return False

        for maybe in self.card_items(need_id=need_id):
            for item in self.card_items():
                if overlaps(maybe.start, maybe.end, item.start, item.end):
                    return True

        return False

    def for_frontend(self, layout):
        grouped = groupby(self.card_items(), key=lambda i: i.need_id)

        def date(record):
            return layout.format_datetime_range(record.start, record.end)

        def remove(record):
            return layout.csrf_protected_url(
                layout.request.link(
                    VolunteerCartAction('remove', record.need_id)))

        for need_id, records in grouped:
            records = tuple(records)

            yield {
                'need_id': need_id.hex,
                'occasion_id': records[0].occasion_id.hex,
                'remove': remove(records[0]),
                'activity': records[0].activity_title,
                'dates': [date(r) for r in records],
                'need': records[0].need_name
            }


class VolunteerCartAction(object):
    """ Represents a single action for the VolunteerCart. """

    def __init__(self, action, target):
        self.action = action
        self.target = target

    def execute(self, request, cart):
        if self.action == 'add':
            if cart.has(self.target):
                return {
                    'success': False,
                    'message': request.translate(_(
                        "This item is already in your list."
                    ))
                }

            if cart.overlaps(self.target):
                return {
                    'success': False,
                    'message': request.translate(_(
                        "Could not add item. It overlaps with "
                        "another item in your list."
                    ))
                }

            cart.add(self.target)

        elif self.action == 'remove':
            cart.remove(self.target)

        else:
            pass

        return {'success': True}
