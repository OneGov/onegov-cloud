from decimal import Decimal
import transaction
from onegov.pay import Payment, PaymentProvider
from datetime import datetime, timezone


def test_view_payments_as_admin(client) -> None:
    client.login_admin()

    session = client.app.session()

    transaction.begin()
    # Payment 1: Created on Jan 10, 2023 (UTC)
    p1 = Payment(
        source='manual',
        amount=Decimal('10.00'),
        currency='CHF',
        state='open'
    )
    p1.created = datetime(2023, 1, 10, 11, 0, 0, tzinfo=timezone.utc)

    # Payment 2: Created on Jan 12, 2023 (UTC)
    p2 = Payment(
        source='manual',
        amount=Decimal('20.00'),
        currency='CHF',
        state='paid'
    )
    p2.created = datetime(2023, 1, 12, 11, 0, 0, tzinfo=timezone.utc)

    session.add_all((p1, p2))
    transaction.commit()

    payments_url = '/payments'

    page = client.get(payments_url)
    return

    # Scenario 1: Filter for Jan 10, 2023. Expect P1.
    form = page.form
    form['start_date'] = '2023-01-10'
    form['end_date'] = '2023-01-10'
    filtered_page = form.submit().follow()
    assert '10.00' in filtered_page.text
    assert '20.00' not in filtered_page.text
    assert "No payments found." not in filtered_page.text

    # Scenario 2: Filter for Jan 10, 2023 to Jan 12, 2023. Expect P1 and P2.
    page = client.get(payments_url)
    form = page.form
    form['start_date'] = '2023-01-10'
    form['end_date'] = '2023-01-12'
    filtered_page = form.submit().follow()
    assert '10.00' in filtered_page.text
    assert '20.00' in filtered_page.text
    assert "No payments found." not in filtered_page.text


def test_view_payments_filter_by_status(client) -> None:
    client.login_admin()

    session = client.app.session()

    transaction.begin()
    # Payment 1: Open
    p1 = Payment(
        source='manual',
        amount=Decimal('10.00'),
        currency='CHF',
        state='open'
    )
    # Payment 2: Paid
    p2 = Payment(
        source='manual',
        amount=Decimal('20.00'),
        currency='CHF',
        state='paid'
    )
    session.add_all((p1, p2))
    transaction.commit()

    payments_url = '/payments'
    page = client.get(payments_url)

    form = page.form
    form['status'] = 'open'
    filtered_page = form.submit().follow()
    assert '10.00' in filtered_page.text
    assert '20.00' not in filtered_page.text
    assert "No payments found." not in filtered_page.text


def test_view_payments_filter_by_payment_type(client) -> None:
    client.login_admin()

    session = client.app.session()

    transaction.begin()
    # Payment 1: Manual
    p1 = Payment(
        source='manual',
        amount=Decimal('30.00'),
        currency='CHF',
        state='open'
    )
    # Payment 2: Provider
    provider = PaymentProvider(type='stripe_connect')
    session.add(provider)
    session.flush()
    p2 = Payment(
        source='stripe_connect',  # example provider source
        provider_id=provider.id,  # needs a provider_id to be 'provider' type
        amount=Decimal('40.00'),
        currency='CHF',
        state='paid'
    )
    session.add_all((p1, p2))
    transaction.commit()

    payments_url = '/payments'
    page = client.get(payments_url)

    # Filter for manual payments
    form = page.form
    form['payment_type'] = 'manual'
    filtered_page = form.submit().follow()
    assert '30.00' in filtered_page.text
    assert '40.00' not in filtered_page.text
    assert "No payments found." not in filtered_page.text

    # Filter for provider payments
    page = client.get(payments_url)  # Re-fetch or reset form
    form = page.form
    form['payment_type'] = 'provider'
    filtered_page = form.submit().follow()

    assert '30.00' not in filtered_page.text
    assert 'Stripe Connect' in filtered_page.text
    assert "No payments found." not in filtered_page.text
