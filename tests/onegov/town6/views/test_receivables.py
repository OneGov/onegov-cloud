from decimal import Decimal
from onegov.pay import PaymentCollection


def test_view_payments_as_admin(client) -> None:
    client.login_admin()
    session = client.app().session
    payments = PaymentCollection(session)
    payments.add(
        amount=Decimal('123.45'),
        currency='CHF',
        source='manual',
        state='open',
        remote_id='PAYMENT-001'
    )
    session.flush()

    page = client.get('/payments')
    assert page.status_code == 200

    # Check for payment details in the rendered page
    assert 'PAYMENT-001' in page.text
    assert '123.45' in page.text
    assert 'CHF' in page.text
    assert 'manual' in page.text  # Payment.source
    assert 'open' in page.text  # Payment.state
