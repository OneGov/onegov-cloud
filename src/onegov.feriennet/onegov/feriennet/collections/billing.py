import hashlib

from collections import OrderedDict
from decimal import Decimal
from itertools import groupby
from onegov.activity import Activity, Attendee, Booking, Occasion, InvoiceItem
from onegov.activity import BookingCollection, InvoiceItemCollection
from onegov.core.utils import normalize_for_url
from onegov.user import User
from sortedcontainers import SortedDict


class BillingDetails(object):

    __slots__ = (
        'id', 'items', 'paid', 'total', 'title', 'outstanding', 'first'
    )

    def __init__(self, title, items):
        self.title = title
        self.total = Decimal()
        self.outstanding = Decimal()
        self.paid = True
        self.first = None

        def tally(item):
            self.total += item.amount

            if not item.paid:
                self.paid = False
                self.outstanding += item.amount

            if self.first is None:
                self.first = item

            return item

        self.items = {
            group: tuple(groupitems) for group, groupitems
            in groupby((tally(i) for i in items), lambda i: i.group)
        }

        self.id = self.item_id(self.first)

    @staticmethod
    def item_id(item):
        components = (item.invoice, item.username)
        return hashlib.md5('/'.join(components).encode('utf-8')).hexdigest()


class BillingCollection(object):

    def __init__(self, session, period, username=None, expand=False):
        self.session = session
        self.period = period
        self.username = username
        self.expand = expand

        self.invoice_items = InvoiceItemCollection(
            session=session,
            username=username,
            invoice=self.period.id.hex
        )

    @property
    def period_id(self):
        return self.period.id

    def for_period(self, period):
        return self.__class__(self.session, period, self.username, self.expand)

    def for_username(self, username):
        return self.__class__(self.session, self.period, username, self.expand)

    def for_expand(self, expand):
        return self.__class__(self.session, self.period, self.username, expand)

    @property
    def bills(self):
        q = self.invoice_items.query()
        q = q.order_by(
            InvoiceItem.username,
            InvoiceItem.group,
            InvoiceItem.text
        )

        titles = OrderedDict(
            (user.username, user.realname or user.username) for user
            in self.session.query(User.username, User.realname).order_by(
                User.title
            )
        )

        bills = SortedDict(
            lambda username: normalize_for_url(titles[username]))

        for user, items in groupby(q, lambda i: i.username):
            bills[user] = BillingDetails(titles[user], items)

        return bills

    @property
    def total(self):
        return self.invoice_items.total or Decimal("0.00")

    @property
    def outstanding(self):
        return self.invoice_items.outstanding or Decimal("0.00")

    def create_invoices(self, all_inclusive_booking_text=None):
        assert not self.period.finalized

        if self.period.all_inclusive and self.period.booking_cost:
            assert all_inclusive_booking_text

        # delete all existing invoice items
        invoice = self.period.id.hex
        session = self.session
        period = self.period

        for item in self.invoice_items.query():
            assert item.invoice == invoice
            session.delete(item)

        # preload data to avoid more expensive joins
        activities = {
            r.id: r.title
            for r in session.query(Occasion.id, Activity.title).join(Activity)
        }

        attendees = {
            a.id: (a.name, a.username)
            for a in session.query(
                Attendee.id,
                Attendee.name,
                Attendee.username
            )
        }

        # regenerate the bookings
        bookings = BookingCollection(session, period_id=period.id)

        q = bookings.query().with_entities(
            Booking.username,
            Booking.cost,
            Booking.occasion_id,
            Booking.attendee_id,
        )
        q = q.filter(Booking.state == 'accepted')

        # keep track of the attendees which have at least one booking (even
        # if said booking is free)
        actual_attendees = set()

        for booking in q:
            actual_attendees.add(booking.attendee_id)

            if booking.cost:
                session.add(InvoiceItem(
                    username=booking.username,
                    invoice=invoice,
                    group=attendees[booking.attendee_id][0],
                    text=activities[booking.occasion_id],
                    unit=booking.cost,
                    quantity=1
                ))

        # add the all inclusive booking costs if necessary
        if period.all_inclusive and period.booking_cost:
            for id, (attendee, username) in attendees.items():
                if id in actual_attendees:
                    session.add(InvoiceItem(
                        username=username,
                        invoice=invoice,
                        group=attendee,
                        text=all_inclusive_booking_text,
                        unit=period.booking_cost,
                        quantity=1
                    ))
