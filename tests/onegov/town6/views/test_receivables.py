from decimal import Decimal
import transaction
from onegov.pay import PaymentCollection


def test_view_payments_as_admin(client) -> None:
    client.login_admin()
    session = client.app.session()
    payments = PaymentCollection(session)
    transaction.begin()
    payments.add(
        amount=Decimal('123.45'),
        currency='CHF',
        source='manual',
        state='open',
        remote_id='PAYMENT-001'
    )
    transaction.commit()
    page = client.get('/payments')
    assert page.status_code == 200

