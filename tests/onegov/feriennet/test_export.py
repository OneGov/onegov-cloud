from __future__ import annotations

import transaction

from onegov.activity import BookingPeriodCollection
from onegov.activity import BookingPeriodInvoiceCollection
from datetime import date
from onegov.core.utils import Bunch
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.exports.booking import BookingExport
from onegov.feriennet.exports.invoiceitem import InvoiceItemExport
from onegov.pay import InvoiceReference
from sqlalchemy import func


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from uuid import UUID
    from .conftest import Client, Scenario


def test_exports(client: Client, scenario: Scenario) -> None:
    # add old period
    scenario.add_period(
        confirmed=True,
        all_inclusive=False,
        active=False
    )

    # We simulate the creation of the same activity in another period earlier
    # The db constraints a unique name, but by changing the title later,
    # we end up with the situation we test here
    scenario.add_activity(
        title="Foobar",
        name='foofoobar',
        state='accepted', tags=['CAMP']
    )

    scenario.add_period(
        confirmed=True,
        all_inclusive=False
    )
    # Add booking user
    scenario.add_user(
        username='member@example.org',
        role='member',
        complete_profile=True
    )
    scenario.add_attendee(
        name='George',
        username='member@example.org',
        differing_address=True,
        address='Whatroad 12',
        zip_code='4040',
        place='Someplace',
        swisspass='123-456-789-0',
        political_municipality='Someotherplace'
    )

    scenario.add_activity(
        title="Foobar", state='accepted', tags=['CAMP', 'Family Camp'])
    scenario.add_occasion()

    # Adding another occasion in the same period for the activity to test
    # export of InvoiceItems when joined with activities filtered by the occ
    # occasion of that period
    scenario.add_occasion()
    scenario.add_booking(state='accepted', cost=250)
    scenario.commit()
    scenario.refresh()

    session = scenario.session
    periods = BookingPeriodCollection(session)
    period = scenario.latest_period
    assert period is not None

    # create a mock request
    def invoice_collection(
        user_id: UUID | None = None,
        period_id: UUID | None = None
    ) -> BookingPeriodInvoiceCollection:
        return BookingPeriodInvoiceCollection(
            session,
            user_id=user_id,
            period_id=period_id
        )

    def request(admin: bool) -> Any:
        return Bunch(
            app=Bunch(
                active_period=periods.active(),
                org=Bunch(
                    geo_provider='geo-mapbox',
                    open_files_target_blank=True
                ),
                invoice_collection=invoice_collection,
                periods=periods.query().all(),
            ),
            session=session,
            include=lambda *args: None,
            model=Bunch(period_id=period.id),
            is_admin=admin,
            is_organiser_only=True if not admin else False,
            is_manager=True if admin else False,
            translate=lambda text, *args, **kwargs: text,
            locale='de_CH',
            current_username=(
                admin and 'admin@example.org'
                or 'organiser@example.org'
            )
        )

    # Export bookings
    rows = BookingExport().run(
        form=Bunch(selected_period=scenario.latest_period),  # type: ignore[arg-type]
        session=session
    )
    data = dict(list(rows)[0])
    assert data['Activity Tags'] == "CAMP\nFamily Camp"
    assert data['Attendee Place'] == 'Someplace'
    assert data['Attendee SwissPass ID'] == '123-456-789-0'
    assert data['Attendee Political Municipality'] == 'Someotherplace'

    # Create invoices
    assert scenario.latest_period is not None
    bills = BillingCollection(
        request(admin=True),
        scenario.latest_period
    )

    bills.create_invoices()

    # Export invoice items with tags
    items = InvoiceItemExport().run(
        form=Bunch(selected_period=scenario.latest_period),  # type: ignore[arg-type]
        session=session
    )
    data = dict(list(items)[0])
    assert data['Activity Tags'] == "CAMP\nFamily Camp"

    invoices = BookingPeriodInvoiceCollection(
        session,
        scenario.latest_period.id
    )
    invoice = invoices.query().first()
    assert invoice is not None
    invoice.references.append(InvoiceReference(
        reference='zzzzzAAAAaaaa',
        schema='esr-v1',
        bucket='esr-v1'
    ))

    invoice_items = invoices.query_items()

    # Mark items as paid
    for item in invoice_items:
        item.paid = True
        item.payment_date = date(2020, 3, 5)

    # Write the item.group of one item in CAPS since this can apparently happen
    invoice_items[0].group = func.upper(invoice_items[0].group)

    transaction.commit()
    scenario.refresh()

    # Export invoice items with tags
    items_ = list(InvoiceItemExport().run(
        form=Bunch(selected_period=scenario.latest_period),  # type: ignore[arg-type]
        session=session
    ))

    # Prevent double exporting each invoice item when joined with the
    # references on invoice if there are multiple references which is
    # not an edge case
    assert len(items_) == 1
    data = dict(items_[0])
    assert len(data['Invoice Item References'].splitlines()) == 2
    assert data['Attendee Address'] == 'Whatroad 12'
    assert data['Attendee Zipcode'] == '4040'
    assert data['Attendee Place'] == 'Someplace'
    assert data['Attendee Political Municipality'] == 'Someotherplace'
    assert data['Attendee SwissPass ID'] == '123-456-789-0'
    assert data['Invoice Item Payment date'] == date(2020, 3, 5)
