import transaction
from datetime import datetime
from freezegun import freeze_time
import textwrap
from onegov.reservation import ResourceCollection


def _create_ticket_and_set_payment_state(
    client,
    allocations_for_date,
    email,
    expected_price_no_donation,
    expected_price_donation
):
    """Helper function to create a reservation and process its ticket."""
    reserve = client.bound_reserve(allocations_for_date[0])

    # Create a reservation
    reserve(quota=2, whole_day=True)  # Sets reservation in session

    initial_form_page = client.get('/resource/tageskarte/form')
    initial_form_page.form['email'] = email
    initial_form_page.form['donation'] = 'No'
    confirmation_page_no_donation = initial_form_page.form.submit().follow()
    assert expected_price_no_donation in confirmation_page_no_donation.text

    initial_form_page.form['donation'] = 'Yes'
    confirmation_page_yes_donation = initial_form_page.form.submit().follow()
    assert expected_price_donation in confirmation_page_yes_donation.text

    # Submit the reservation, this creates the ticket
    # The ticket is created by the currently logged-in user.
    ticket_page = confirmation_page_yes_donation.form.submit().follow()
    assert 'RSV-' in ticket_page.text

    # Editor accepts the ticket.
    # Assumes the new ticket is the first one in the 'open' list.
    accepted_ticket_page = client.get(
        '/tickets/ALL/open').click("Annehmen").follow()
    assert email in accepted_ticket_page.text  # Verify correct ticket

    assert accepted_ticket_page.pyquery('.payment-state').text() == "Offen"

    client.post(accepted_ticket_page.pyquery('.mark-as-paid').attr('ic-post-to'))
    page_after_paid = client.get(accepted_ticket_page.request.url)
    assert page_after_paid.pyquery('.payment-state').text() == "Bezahlt"

    client.post(page_after_paid.pyquery('.mark-as-unpaid').attr('ic-post-to'))
    page_after_unpaid = client.get(page_after_paid.request.url)
    assert page_after_unpaid.pyquery('.payment-state').text() == "Offen"

    return page_after_unpaid


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

    # Login as editor once before ticket creation and processing
    client.login_editor()

    # First reservation (created on 2017-07-09)
    allocations_d1 = scheduler.allocate(
        dates=(
            datetime(2017, 7, 9),
            datetime(2017, 7, 9)
        ),
        whole_day=True,
        quota=4
    )
    transaction.commit()
    _create_ticket_and_set_payment_state(
        client, allocations_d1, 'info@example.org', '30.00', '40.00'
    )

    # Second reservation (created on 2017-07-08)
    with freeze_time("2017-07-08", tick=True):
        allocations_d2 = scheduler.allocate(
            dates=(
                datetime(2017, 7, 8),  # Reservation for July 8th
                datetime(2017, 7, 8)
            ),
            whole_day=True,
            quota=4
        )
        transaction.commit()
        _create_ticket_and_set_payment_state(
            client, allocations_d2, 'other_user@example.org', '30.00', '40.00'
        )

    payments = client.get('/payments')
    payments .showbrowser()
    assert "RSV-" in payments
    assert "Manuell" in payments
    assert "info@example.org" in payments
    assert "other_user@example.org" in payments
    assert "40.00" in payments
    assert "Offen" in payments

    # We have now two payments:
    # 1. For info@example.org, created on 2017-07-09
    # 2. For other_user@example.org, created on 2017-07-08
