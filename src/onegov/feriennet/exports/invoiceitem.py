from __future__ import annotations

from onegov.activity import (
    BookingPeriodInvoice, ActivityInvoiceItem, Activity, Occasion, Attendee)
from onegov.core.security import Secret
from onegov.feriennet import FeriennetApp, _
from onegov.feriennet.exports.base import FeriennetExport
from onegov.feriennet.forms import PeriodExportForm
from onegov.user import User
from sqlalchemy.orm import contains_eager
from sqlalchemy import distinct
from sqlalchemy import or_


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from onegov.activity.models import BookingPeriod
    from sqlalchemy.orm import Query, Session


@FeriennetApp.export(
    id='rechnungspositionen',
    form_class=PeriodExportForm,
    permission=Secret,
    title=_('Invoice Items'),
    explanation=_('Exports invoice items in the given period.'),
)
class InvoiceItemExport(FeriennetExport):

    def run(
        self,
        form: PeriodExportForm,  # type:ignore[override]
        session: Session
    ) -> Iterator[Iterator[tuple[str, Any]]]:

        assert form.selected_period is not None
        return self.rows(session, form.selected_period)

    def rows(
        self,
        session: Session,
        period: BookingPeriod
    ) -> Iterator[Iterator[tuple[str, Any]]]:
        for item, tags, attendee in self.query(session, period):
            yield ((k, v) for k, v in self.fields(item, tags, attendee))

    def query(
        self,
        session: Session,
        period: BookingPeriod
    ) -> Query[tuple[ActivityInvoiceItem, list[str] | None, Attendee]]:

        # There might be activities with same title from other periods
        # resulting in double entries of invoice items
        # We filter by the period in order to get the correct tags
        activities = session.query(
            distinct(Activity.title).label('title'),
            Activity._tags.label('tags')
        ).join(Occasion).filter(
            Occasion.period_id == period.id
        )
        activities = activities.subquery()

        q = session.query(ActivityInvoiceItem, activities.c.tags, Attendee)
        q = q.join(BookingPeriodInvoice).join(User)
        q = q.outerjoin(
            activities, ActivityInvoiceItem.text == activities.c.title
        ).outerjoin(
            Attendee, ActivityInvoiceItem.attendee_id == Attendee.id
        )
        q = q.options(
            contains_eager(ActivityInvoiceItem.invoice)
            .contains_eager(BookingPeriodInvoice.user)
            .undefer(User.data))
        q = q.filter(BookingPeriodInvoice.period_id == period.id)
        q = q.filter(or_(User.username == Attendee.username,
                         Attendee.username.is_(None)))
        q = q.filter(User.id == BookingPeriodInvoice.user_id)
        q = q.order_by(
            User.username,
            ActivityInvoiceItem.group,
            ActivityInvoiceItem.text
        )
        return q

    def fields(
        self,
        item: ActivityInvoiceItem,
        tags: list[str] | None,
        attendee: Attendee
    ) -> Iterator[tuple[str, Any]]:

        yield from self.invoice_item_fields(item)
        yield from self.user_fields(item.invoice.user)
        yield from self.activity_tags(tags)
        yield from self.invoice_attendee_fields(attendee)
