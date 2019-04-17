from collections import OrderedDict
from decimal import Decimal
from itertools import groupby
from onegov.activity import Activity, Attendee, Booking, Occasion
from onegov.activity import Invoice, InvoiceItem, InvoiceReference
from onegov.activity import BookingCollection
from onegov.core.orm import as_selectable_from_path
from onegov.core.utils import module_path, Bunch
from onegov.user import User
from sqlalchemy import select
from sqlalchemy.orm import joinedload
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

    def add_position(self, users, text, amount, group):

        # only add these positions to people who actually have an invoice
        invoices = self.invoices.query()\
            .outerjoin(User)\
            .filter(User.username.in_(users))

        # each time we add a position, we group it uniquely using a family
        family = f"{group}-{ulid()}"
        count = 0

        for invoice in invoices:
            count += 1
            invoice.add(
                group=group,
                text=text,
                unit=amount,
                quantity=1,
                paid=False,
                family=family
            )

        return count

    def add_manual_position(self, users, text, amount):
        return self.add_position(users, text, amount, group='manual')

    def include_donation(self, text, user_id, amount):
        """ Includes a donation for the given user and period.

        Unlike manual positions, donations are supposed to be off/on per
        period. Therefore this interface is somewhat different and has an
        exclude_donation counterpart.

        """

        # an invoice is required
        invoice = self.invoices.query()\
            .outerjoin(User)\
            .filter(User.id == user_id)\
            .options(joinedload(Invoice.items))\
            .one()

        # if there's an existing donation, update it
        for item in invoice.items:
            if item.group == 'donation':
                assert not item.paid

                item.unit = amount
                item.text = text
                return

        # if there's no donation, add it
        return invoice.add(
            group='donation',
            text=text,
            unit=amount,
            quantity=1,
            paid=False
        )

    def exclude_donation(self, user_id):
        invoice = self.invoices.query()\
            .outerjoin(User)\
            .filter(User.id == user_id)\
            .options(joinedload(Invoice.items))\
            .first()

        if not invoice:
            return

        donations = (i for i in invoice.items if i.group == 'donation')
        donation = next(donations, None)

        if donation:
            assert not donation.paid
            self.session.delete(donation)

    def create_invoices(self, all_inclusive_booking_text=None):
        assert not self.period.finalized

        if self.period.all_inclusive and self.period.booking_cost:
            assert all_inclusive_booking_text

        # speed up some lookups
        session = self.session
        period = self.period
        invoices = self.invoices

        # delete all existing invoices
        invoice_ids = invoices.query().with_entities(Invoice.id).subquery()

        def delete_queries():
            yield session.query(InvoiceReference).filter(
                InvoiceReference.invoice_id.in_(invoice_ids))

            yield session.query(InvoiceItem).filter(
                InvoiceItem.invoice_id.in_(invoice_ids))

            yield invoices.query()

        for q in delete_queries():
            q.delete('fetch')

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
                    user_id=users[booking.username],
                    flush=False,
                    optimistic=True
                )

            if period.pay_organiser_directly or not booking.cost:
                continue

            created_invoices[booking.username].add(
                group=attendees[booking.attendee_id][0],
                text=activities[booking.occasion_id],
                unit=booking.cost,
                quantity=1,
                flush=False
            )

        # add the all inclusive booking costs if necessary
        if period.all_inclusive and period.booking_cost:
            for id, (attendee, username) in attendees.items():
                if id in actual_attendees:
                    created_invoices[username].add(
                        group=attendee,
                        text=all_inclusive_booking_text,
                        unit=period.booking_cost,
                        quantity=1,
                        flush=False
                    )
