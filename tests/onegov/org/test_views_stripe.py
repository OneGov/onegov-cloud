import textwrap

import requests_mock
import transaction
from purl import URL

from onegov.form import FormCollection
from onegov.pay import PaymentProviderCollection


def test_setup_stripe(client):
    client.login_admin()

    assert client.app.default_payment_provider is None

    with requests_mock.Mocker() as m:
        m.post('https://oauth.example.org/register/foo', json={
            'token': '0xdeadbeef'
        })

        client.get('/payment-provider').click("Stripe Connect")

        url = URL(m.request_history[0].json()['url'])
        url = url.query_param('oauth_redirect_secret', 'bar')
        url = url.query_param('code', 'api_key')

        m.post('https://connect.stripe.com/oauth/token', json={
            'scope': 'read_write',
            'stripe_publishable_key': 'stripe_publishable_key',
            'stripe_user_id': 'stripe_user_id',
            'refresh_token': 'refresh_token',
            'access_token': 'access_token',
        })

        client.get(url.as_string())

    provider = client.app.default_payment_provider
    assert provider.title == 'Stripe Connect'
    assert provider.publishable_key == 'stripe_publishable_key'
    assert provider.user_id == 'stripe_user_id'
    assert provider.refresh_token == 'refresh_token'
    assert provider.access_token == 'access_token'


def test_stripe_form_payment(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Donate', definition=textwrap.dedent("""
        E-Mail *= @@@

        Donation *=
            (x) Small (10 CHF)
            ( ) Medium (100 CHF)
    """), type='custom', payment_method='free')

    providers = PaymentProviderCollection(client.app.session())
    providers.add(type='stripe_connect', default=True, meta={
        'publishable_key': '0xdeadbeef',
        'access_token': 'foobar'
    })

    transaction.commit()

    page = client.get('/form/donate')
    page.form['e_mail'] = 'info@example.org'
    page = page.form.submit().follow()

    assert "Totalbetrag" in page
    assert "10.00 CHF" in page
    assert "+ 0.59" not in page
    assert "Online zahlen und abschliessen" in page

    button = page.pyquery('.checkout-button')
    assert button.attr('data-stripe-amount') == '1000'
    assert button.attr('data-stripe-currency') == 'CHF'
    assert button.attr('data-stripe-email') == 'info@example.org'
    assert button.attr('data-stripe-description') == 'Donate'
    assert button.attr('data-action') == 'submit'
    assert button.attr('data-stripe-allowrememberme') == 'false'
    assert button.attr('data-stripe-key') == '0xdeadbeef'

    with requests_mock.Mocker() as m:
        charge = {
            'id': '123456'
        }

        m.post('https://api.stripe.com/v1/charges', json=charge)
        m.get('https://api.stripe.com/v1/charges/123456', json=charge)
        m.post('https://api.stripe.com/v1/charges/123456/capture', json=charge)

        page.form['payment_token'] = 'foobar'
        page.form.submit().follow()

    with requests_mock.Mocker() as m:
        m.get('https://api.stripe.com/v1/charges/123456', json={
            'id': '123456',
            'captured': True,
            'refunded': False,
            'paid': True,
            'status': 'foobar'
        })

        client.login_admin()
        ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
        assert "Bezahlt" in ticket

    payments = client.get('/payments')
    assert "FRM-" in payments
    assert "Stripe Connect" in payments
    assert "info@example.org" in payments
    assert "9.41 CHF" in payments
    assert "0.59" in payments


def test_stripe_charge_fee_to_customer(client):
    collection = FormCollection(client.app.session())
    collection.definitions.add('Donate', definition=textwrap.dedent("""
        E-Mail *= @@@

        Donation *=
            (x) Small (10 CHF)
            ( ) Medium (100 CHF)
    """), type='custom', payment_method='free')

    providers = PaymentProviderCollection(client.app.session())
    providers.add(type='stripe_connect', default=True, meta={
        'publishable_key': '0xdeadbeef',
        'access_token': 'foobar',
        'user_id': 'foobar'
    })

    transaction.commit()

    client.login_admin()

    with requests_mock.Mocker() as m:
        m.get('https://api.stripe.com/v1/accounts/foobar', json={
            'business_name': 'Govikon',
            'email': 'info@example.org'
        })

        page = client.get('/payment-provider').click("Einstellungen", index=1)

    assert 'Govikon / info@example.org' in page
    page.form['charge_fee_to_customer'] = True
    page.form.submit()

    page = client.get('/form/donate')
    page.form['e_mail'] = 'info@example.org'
    page = page.form.submit().follow()

    assert "Totalbetrag" in page
    assert "10.00 CHF" in page
    assert "+ 0.61 CHF Kreditkarten-Gebühr" in page
    assert "Online zahlen und abschliessen" in page

    button = page.pyquery('.checkout-button')
    assert button.attr('data-stripe-amount') == '1061'

    with requests_mock.Mocker() as m:
        charge = {
            'id': '123456'
        }

        m.post('https://api.stripe.com/v1/charges', json=charge)
        m.get('https://api.stripe.com/v1/charges/123456', json=charge)
        m.post('https://api.stripe.com/v1/charges/123456/capture', json=charge)

        page.form['payment_token'] = 'foobar'
        page.form.submit().follow()

    with requests_mock.Mocker() as m:
        m.get('https://api.stripe.com/v1/charges/123456', json={
            'id': '123456',
            'captured': True,
            'refunded': False,
            'paid': True,
            'status': 'foobar'
        })

        client.login_admin()
        ticket = client.get('/tickets/ALL/open').click('Annehmen').follow()
        assert "Bezahlt" in ticket

    payments = client.get('/payments')
    assert "FRM-" in payments
    assert "Stripe Connect" in payments
    assert "info@example.org" in payments
    assert "10.00" in payments
    assert "0.61" in payments
