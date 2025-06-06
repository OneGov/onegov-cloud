from decimal import Decimal
import transaction
from onegov.pay import Payment
from datetime import datetime

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.town6.tests import Client


def test_view_payments_as_admin(client: 'Client') -> None:
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
    p1.created = datetime(2023, 1, 10, 11, 0, 0)  # Naive UTC

    # Payment 2: Created on Jan 12, 2023 (UTC)
    p2 = Payment(
        source='manual',
        amount=Decimal('20.00'),
        currency='CHF',
        state='paid'
    )
    p2.created = datetime(2023, 1, 12, 11, 0, 0)  # Naive UTC

    session.add_all((p1, p2))
    transaction.commit()

    payments_url = '/payments'

    # Get initial page to obtain CSRF token
    page = client.get(payments_url)
    assert page.status_code == 200
    assert '10.00' in page.text
    assert '20.00' in page.text
    csrf_token = page.form['_csrf_token'].value

    # Scenario 1: Filter for Jan 10, 2023. Expect P1.
    form_data = {
        'start_date': '2023-01-10',
        'end_date': '2023-01-10',
        'status': '',
        'payment_type': '',
        '_csrf_token': csrf_token
    }
    response = client.post(payments_url, data=form_data)
    assert response.status_code == 302  # Expect a redirect
    filtered_page = client.get(response.headers['Location'])
    assert '10.00' in filtered_page.text
    assert '20.00' not in filtered_page.text
    assert "No payments found." not in filtered_page.text

    # Scenario 2: Filter for Jan 10, 2023 to Jan 12, 2023. Expect P1 and P2.
    form_data['end_date'] = '2023-01-12'
    response = client.post(payments_url, data=form_data)
    assert response.status_code == 302
    filtered_page = client.get(response.headers['Location'])
    assert '10.00' in filtered_page.text
    assert '20.00' in filtered_page.text
    assert "No payments found." not in filtered_page.text

    # Scenario 3: Filter for Jan 11, 2023 (a day with no payments). Expect none.
    form_data['start_date'] = '2023-01-11'
    form_data['end_date'] = '2023-01-11'
    response = client.post(payments_url, data=form_data)
    assert response.status_code == 302
    filtered_page = client.get(response.headers['Location'])
    assert '10.00' not in filtered_page.text
    assert '20.00' not in filtered_page.text
    assert "No payments found." in filtered_page.text

    # Scenario 4: Filter for Jan 12, 2023. Expect P2.
    form_data['start_date'] = '2023-01-12'
    form_data['end_date'] = '2023-01-12'
    response = client.post(payments_url, data=form_data)
    assert response.status_code == 302
    filtered_page = client.get(response.headers['Location'])
    assert '10.00' not in filtered_page.text
    assert '20.00' in filtered_page.text
    assert "No payments found." not in filtered_page.text

    # Scenario 5: No date filter (clear dates). Expect P1 and P2.
    form_data['start_date'] = ''
    form_data['end_date'] = ''
    response = client.post(payments_url, data=form_data)
    assert response.status_code == 302
    filtered_page = client.get(response.headers['Location'])
    assert '10.00' in filtered_page.text
    assert '20.00' in filtered_page.text
    assert "No payments found." not in filtered_page.text

