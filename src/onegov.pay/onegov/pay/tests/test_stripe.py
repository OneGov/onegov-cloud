import pytest

from onegov.pay.models.payment_providers import StripeConnect
from unittest import mock


def test_oauth_url():
    provider = StripeConnect(client_id='foo', client_secret='bar')

    url = provider.oauth_url('https://handle-incoming-request')
    assert 'response_type=code' in url
    assert 'handle-incoming-request' in url
    assert 'scope=read_write' in url
    assert 'client_id=foo' in url
    assert 'client_secret=bar' in url

    url = provider.oauth_url('https://foo', {'email': 'foo@bar.org'})
    assert 'stripe_user%5Bemail%5D=foo%40bar.org' in url


def test_process_oauth_response():
    provider = StripeConnect(client_id='foo', client_secret='bar')

    with pytest.raises(RuntimeError) as e:
        provider.process_oauth_response(
            {
                'error': 'foo',
                'error_description': 'bar'
            }
        )

    assert e.value.args == ('Stripe OAuth request failed (foo: bar)', )

    with mock.patch('stripe.OAuth.token', return_value={
        'scope': 'read_write',
        'stripe_publishable_key': 'pubkey',
        'stripe_user_id': 'uid',
        'refresh_token': 'rtoken',
        'access_token': 'atoken',
    }):
        provider.process_oauth_response({'code': '0xdeadbeef'})

        assert provider.publishable_key == 'pubkey'
        assert provider.user_id == 'uid'
        assert provider.refresh_token == 'rtoken'
        assert provider.access_token == 'atoken'
