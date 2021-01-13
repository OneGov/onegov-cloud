from onegov.activity import InvoiceCollection, PeriodCollection
from onegov.core.utils import Bunch
from onegov.feriennet.collections import BillingCollection
from onegov.feriennet.exports.booking import BookingExport
from onegov.feriennet.exports.invoiceitem import InvoiceItemExport


def test_exports(client, scenario):
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
                org=Bunch(geo_provider='geo-mapbox'),
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
    data = {k: v for k, v in list(rows)[0]}
    assert data['Activity Tags'] == "Family Camp"

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
    data = {k: v for k, v in list(items)[0]}
    assert data['Activity Tags'] == "CAMP\nFamily Camp"
