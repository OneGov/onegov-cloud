from decimal import Decimal
from onegov.pay import PaymentCollection
from tests.shared.utils import create_image
from onegov.core.utils import module_path


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.testing.client import Client


def test_view_payments_as_admin(client: 'Client') -> None:
    client.login_admin()

    # Create a payment
    payments = PaymentCollection(client.session)
    payments.add(
        amount=Decimal('123.45'),
        currency='CHF',
        source='manual',
        state='open',
        remote_id='PAYMENT-001'
    )
    client.session.flush()

    page = client.get('/payments')
    assert page.status_code == 200

    # Check for payment details in the rendered page
    assert 'PAYMENT-001' in page.text
    assert '123.45' in page.text
    assert 'CHF' in page.text
    assert 'manual' in page.text  # Payment.source
    assert 'open' in page.text  # Payment.state
