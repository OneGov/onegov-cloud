from collections import OrderedDict
from decimal import Decimal
from itertools import groupby
from onegov.activity import Activity, Attendee, Booking, Occasion
from onegov.activity import BookingCollection
from onegov.core.orm import as_selectable_from_path
from onegov.core.utils import module_path, Bunch
from onegov.user import User
from sqlalchemy import select
from ulid import ulid


class BillingCollection(object):

    def __init__(self, request, period, username=None, expand=False):
        self.request = request
        self.session = request.session
        self.app = request.app
        self.period = period
        self.username = username
        self.expand = expand
        self.invoices = request.app.invoice_collection(
            user_id=self.user_id,
            period_id=self.period.id
        )

    @property
    def user_id(self):
        if self.username:
            return self.app.user_ids_by_name[self.username]

    @property
    def period_id(self):
        return self.period.id

    def for_period(self, period):
        return self.__class__(self.request, period, self.username, self.expand)

    def for_username(self, username):
        return self.__class__(self.request, self.period, username, self.expand)

    def for_expand(self, expand):
        return self.__class__(self.request, self.period, self.username, expand)

    @property
    def invoices_by_period_query(self):
        return as_selectable_from_path(
            module_path('onegov.feriennet', 'queries/invoices_by_period.sql'))

    @property
    def invoices_by_period(self):
        invoices = self.invoices_by_period_query.c

        query = select(invoices).where(invoices.period_id == self.period_id)

        if self.username:
            query = query.where(invoices.username == self.username)

        return self.session.execute(query)

    @property
    def bills(self):
        bills = OrderedDict()
        invoices = self.invoices_by_period

        for username, items in groupby(invoices, lambda i: i.username):
            items = tuple(items)
            first = items[0]

            bills[username] = Bunch(
                items=items,
                first=first,
                id=first.id,
                invoice_id=first.invoice_id,
                title=first.realname or first.username,
                paid=first.invoice_paid,
                total=first.invoice_amount,
                outstanding=first.invoice_outstanding,
                discourage_changes=first.invoice_changes == 'discouraged',
                disable_changes=first.invoice_changes == 'impossible',
                has_online_payments=first.has_online_payments
            )

        return bills

    @property
    def total(self):
        # bills can technically be negative, which is not useful for us
        zero = Decimal("0.00")
        return max(zero, self.invoices.total_amount or zero)

    @property
    def outstanding(self):
        zero = Decimal("0.00")
        return max(zero, self.invoices.outstanding_amount or zero)

    def add_manual_position(self, users, text, amount):

        # only add these positions to people who actually have an invoice
        invoices = self.invoices.query()\
            .outerjoin(User)\
            .filter(User.username.in_(users))

        # each time we add a manual position, we group it using a family
        family = f"manual-{ulid()}"
        count = 0

        for invoice in invoices:
            count += 1
            invoice.add(
                group='manual',
                text=text,
                unit=amount,
                quantity=1,
                paid=False,
                family=family
            )

        return count

    def create_invoices(self, all_inclusive_booking_text=None):
        assert not self.period.finalized

        if self.period.all_inclusive and self.period.booking_cost:
            assert all_inclusive_booking_text

        # speed up some lookups
        session = self.session
        period = self.period
        invoices = self.invoices

        # delete all existing invoices
        for invoice in self.invoices.query():
            assert invoice.period_id == self.period.id
            session.delete(invoice)

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

        # regenerate the invoices
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

        # keep track of the invoices which were created
        created_invoices = {}

        # easy user_id lookup
        users = dict(session.query(User).with_entities(User.username, User.id))

        for booking in q:
            actual_attendees.add(booking.attendee_id)

            if booking.username not in created_invoices:
                created_invoices[booking.username] = invoices.add(
                    period_id=period.id,
                    user_id=users[booking.username]
                )

            if period.pay_organiser_directly or not booking.cost:
                continue

            created_invoices[booking.username].add(
                group=attendees[booking.attendee_id][0],
                text=activities[booking.occasion_id],
                unit=booking.cost,
                quantity=1
            )

        # add the all inclusive booking costs if necessary
        if period.all_inclusive and period.booking_cost:
            for id, (attendee, username) in attendees.items():
                if id in actual_attendees:
                    created_invoices[booking.username].add(
                        group=attendee,
                        text=all_inclusive_booking_text,
                        unit=period.booking_cost,
                        quantity=1
                    )
