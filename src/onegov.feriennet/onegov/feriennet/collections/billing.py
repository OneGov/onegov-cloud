from collections import OrderedDict
from itertools import groupby
from decimal import Decimal
from onegov.activity import Activity, Attendee, Booking, Occasion, InvoiceItem
from onegov.activity import BookingCollection, InvoiceItemCollection


class BillingCollection(object):

    def __init__(self, session, period):
        self.session = session
        self.period = period

        self.invoice_items = InvoiceItemCollection(
            session=session,
            invoice=self.period.id.hex
        )

    @property
    def period_id(self):
        return self.period.id

    def for_period(self, period):
        return self.__class__(self.session, period)

    @property
    def bills(self):
        q = self.invoice_items.query()
        q = q.order_by(
            InvoiceItem.username,
            InvoiceItem.group,
            InvoiceItem.text
        )

        bills = OrderedDict()

        for username, items in groupby(q, lambda i: i.username):
            bills[username] = tuple(items)

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

        for booking in q:
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
            for attendee, username in attendees.values():
                session.add(InvoiceItem(
                    username=username,
                    invoice=invoice,
                    group=attendee,
                    text=activities[booking.occasion_id],
                    unit=period.booking_cost,
                    quantity=1
                ))
