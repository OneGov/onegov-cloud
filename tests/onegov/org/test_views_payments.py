import transaction
from datetime import datetime
from freezegun import freeze_time
import textwrap
from onegov.reservation import ResourceCollection



@freeze_time("2017-07-09", tick=True)
def test_filter_by_ticket_date_in_payments(client):
    # prepate the required data
    resources = ResourceCollection(client.app.libres_context)
    resource = resources.by_name('tageskarte')
    resource.pricing_method = 'per_item'
    resource.price_per_item = 15.00
    resource.extras_pricing_method = 'one_off'
    resource.payment_method = 'manual'
    resource.definition = textwrap.dedent("""
        Donation =
            (x) Yes (10 CHF)
            ( ) No
    """)

    scheduler = resource.get_scheduler(client.app.libres_context)
    allocations = scheduler.allocate(
        dates=(
            datetime(2017, 7, 9),
            datetime(2017, 7, 9)
        ),
        whole_day=True,
        quota=4
    )

    reserve = client.bound_reserve(allocations[0])
    transaction.commit()

    # create a reservation
    reserve(quota=2, whole_day=True)
    page = client.get('/resource/tageskarte/form')
    page.form['email'] = 'info@example.org'
    page.form['donation'] = 'No'
    assert '30.00' in page.form.submit().follow()

    page.form['donation'] = 'Yes'
    assert '40.00' in page.form.submit().follow()

    ticket = page.form.submit().follow().form.submit().follow()
    assert 'RSV-' in ticket.text

    # mark it as paid
    client.login_editor()
    page = client.get('/tickets/ALL/open').click("Annehmen").follow()

    assert page.pyquery('.payment-state').text() == "Offen"

    client.post(page.pyquery('.mark-as-paid').attr('ic-post-to'))
    page = client.get(page.request.url)

    assert page.pyquery('.payment-state').text() == "Bezahlt"

    client.post(page.pyquery('.mark-as-unpaid').attr('ic-post-to'))
    page = client.get(page.request.url)

    assert page.pyquery('.payment-state').text() == "Offen"

    payments = client.get('/payments')
    assert "RSV-" in payments
    assert "Manuell" in payments
    assert "info@example.org" in payments
    assert "40.00" in payments
    assert "Offen" in payments

    # we have now a single payment created 09.07.2017 02:00 
