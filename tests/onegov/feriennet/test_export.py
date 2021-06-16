from onegov.activity import InvoiceCollection, PeriodCollection, \
    InvoiceReference
from onegov.core.utils import Bunch
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.exports.booking import BookingExport
from onegov.feriennet.exports.invoiceitem import InvoiceItemExport


def test_exports(client, scenario):
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
    scenario.add_attendee(name='George', username='member@example.org')

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
    periods = PeriodCollection(session)
    period = scenario.latest_period

    # create a mock request
    def invoice_collection(user_id=None, period_id=None):
        return InvoiceCollection(session, user_id=user_id, period_id=period_id)

    def request(admin):
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
            is_organiser_only=not admin and True or False,
            is_manager=admin and True or False,
            translate=lambda text, *args, **kwargs: text,
            locale='de_CH',
            current_username=(
                    admin and 'admin@example.org' or 'organiser@example.org'
            )
        )

    # Export buchungen
    rows = BookingExport().run(
        form=Bunch(selected_period=scenario.latest_period),
        session=session
    )
    data = dict(list(rows)[0])
    assert data['Activity Tags'] == "CAMP\nFamily Camp"

    # Create invoices
    bills = BillingCollection(
        request(admin=True),
        scenario.latest_period
    )

    bills.create_invoices()

    # Export invoice items with tags
    items = InvoiceItemExport().run(
        form=Bunch(selected_period=scenario.latest_period),
        session=session
    )
    data = dict(list(items)[0])
    assert data['Activity Tags'] == "CAMP\nFamily Camp"

    invoices = InvoiceCollection(session, scenario.latest_period.id)
    invoice = invoices.query().first()
    invoice.references.append(InvoiceReference(
        reference='zzzzzAAAAaaaa',
        schema='esr-v1',
        bucket='esr-v1'
    ))

    # Export invoice items with tags
    items = list(InvoiceItemExport().run(
        form=Bunch(selected_period=scenario.latest_period),
        session=session
    ))

    # Prevent double exporting each invoice item when joined with the
    # references on invoice if there are multiple references which is
    # not an edge case
    assert len(items) == 1
    data = dict(items[0])
    assert len(data['Invoice Item References'].splitlines()) == 2

