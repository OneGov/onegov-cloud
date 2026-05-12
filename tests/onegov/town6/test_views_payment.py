from __future__ import annotations

import json
import transaction

from datetime import datetime, timezone
from decimal import Decimal
from onegov.org.models.ticket import FormSubmissionTicket
from onegov.pay import Payment, PaymentProvider
from onegov.ticket import TicketInvoice
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import Client


def test_view_payments_as_admin(client: Client) -> None:
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

    # Scenario 1: Filter for open payments expect P1
    form = page.form
    form['status'] = 'open'
    filtered_page = form.submit().follow()
    assert '10.00' in filtered_page.text
    assert '20.00' not in filtered_page.text
    assert "No payments found." not in filtered_page.text

    # Scenario 2: Filter for any status, expect P1 and P2
    page = client.get(payments_url)
    form = page.form
    form['status'] = ''
    filtered_page = form.submit().follow()
    assert '10.00' in filtered_page.text
    assert '20.00' in filtered_page.text
    assert "No payments found." not in filtered_page.text


def test_view_payments_filter_by_status(client: Client) -> None:
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


def test_view_payments_filter_by_payment_type(client: Client) -> None:
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


def test_view_payments_invoices_handle_batch_set(client: Client) -> None:
    client.login_admin()
    session = client.app.session()

    transaction.begin()
    open_invoice_ids = []
    invoiced_invoice_ids = []
    for i in range(10):
        state = 'open' if i % 2 == 0 else 'invoiced'

        ticket = FormSubmissionTicket(
            number=f'FRM-{i:04d}-0001',
            title=f'Test Ticket {i}',
            group='Test',
            handler_id=str(uuid4()),
            state='pending',
            handler_data={}
        )
        session.add(ticket)

        invoice = TicketInvoice(id=uuid4())
        session.add(invoice)
        ticket.invoice = invoice

        payment = Payment(
            source='manual',
            amount=Decimal('10.00') + i,
            currency='CHF',
            state=state
        )
        session.add(payment)

        invoice_item = invoice.add(
            group='test',
            text=f'Item {i}',
            unit=Decimal('10.00') + i,
            quantity=Decimal('1')
        )
        invoice_item.payments.append(payment)

        if state == 'open':
            open_invoice_ids.append(str(invoice.id))
        if state == 'invoiced':
            invoice.invoiced = True
            invoiced_invoice_ids.append(str(invoice.id))

    transaction.commit()

    assert session.query(Payment).count() == 10
    assert session.query(Payment).filter_by(state='open').count() == 5
    assert session.query(Payment).filter_by(state='invoiced').count() == 5
    assert session.query(Payment).filter_by(state='paid').count() == 0

    # submit invalid batch state
    page = client.get('/invoices')
    url = page.pyquery('[data-action-url]').attr('data-action-url')
    response = client.post(
        url,
        json.dumps({'invoice_ids': open_invoice_ids[:2], 'state': 'invalid'}),
        content_type='application/json',
        expect_errors=True
    )
    assert response.status_code == 400

    # select two open payments and submit the batch action
    # to mark them as invoiced
    page = client.get('/invoices')
    url = page.pyquery('[data-action-url]').attr('data-action-url')
    selected_ids = open_invoice_ids[:2]
    response = client.post(
        url,
        json.dumps({'invoice_ids': selected_ids, 'state': 'invoiced'}),
        content_type='application/json'
    )
    assert response.status_int == 200

    session.expire_all()
    assert session.query(Payment).filter_by(state='open').count() == 3
    assert session.query(Payment).filter_by(state='invoiced').count() == 7
    assert session.query(Payment).filter_by(state='paid').count() == 0

    # select two invoiced payments and submit the batch action
    # to mark them as paid
    page = client.get('/invoices')
    url = page.pyquery('[data-action-url]').attr('data-action-url')
    assert url
    selected_ids = invoiced_invoice_ids[:2]
    response = client.post(
        url,
        json.dumps({'invoice_ids': selected_ids, 'state': 'paid'}),
        content_type='application/json'
    )
    assert response.status_int == 200

    session.expire_all()
    assert session.query(Payment).filter_by(state='open').count() == 3
    assert session.query(Payment).filter_by(state='invoiced').count() == 5
    assert session.query(Payment).filter_by(state='paid').count() == 2

    # now mark two as uninvoiced
    page = client.get('/invoices')
    url = page.pyquery('[data-action-url]').attr('data-action-url')
    assert url
    selected_ids = invoiced_invoice_ids[2:4]
    response = client.post(
        url,
        json.dumps({'invoice_ids': selected_ids, 'state': 'uninvoiced'}),
        content_type='application/json'
    )
    assert response.status_int == 200

    session.expire_all()
    assert session.query(Payment).filter_by(state='open').count() == 5
    assert session.query(Payment).filter_by(state='invoiced').count() == 3
    assert session.query(Payment).filter_by(state='paid').count() == 2

    # mark two as open again
    page = client.get('/invoices')
    url = page.pyquery('[data-action-url]').attr('data-action-url')
    assert url
    selected_ids = invoiced_invoice_ids[:2]
    response = client.post(
        url,
        json.dumps({'invoice_ids': selected_ids, 'state': 'open'}),
        content_type='application/json'
    )
    assert response.status_int == 200

    session.expire_all()
    assert session.query(Payment).filter_by(state='open').count() == 5
    assert session.query(Payment).filter_by(state='invoiced').count() == 5
    assert session.query(Payment).filter_by(state='paid').count() == 0
