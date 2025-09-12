from __future__ import annotations

import logging
import pytest
import requests_mock
import transaction

from onegov.pay.models.payment_providers.stripe import (
    StripeConnect,
    StripeFeePolicy,
    StripeCaptureManager
)
from purl import URL
from unittest import mock
from urllib.parse import quote


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared.capturelog import CaptureLogFixture


def test_oauth_url() -> None:
    provider = StripeConnect(client_id='foo', client_secret='bar')  # type: ignore[misc]

    url = provider.oauth_url('https://handle-incoming-request')
    assert 'response_type=code' in url
    assert 'handle-incoming-request' in url
    assert 'scope=read_write' in url
    assert 'client_id=foo' in url
    assert 'client_secret=bar' in url

    url = provider.oauth_url('https://foo', 'bar', {'email': 'foo@bar.org'})
    assert 'state=bar' in url
    assert 'stripe_user%5Bemail%5D=foo%40bar.org' in url


def test_process_oauth_response() -> None:
    provider = StripeConnect(  # type: ignore[misc]
        client_id='foo',
        client_secret='bar',
        oauth_gateway='https://oauth.onegovcloud.ch/',
        oauth_gateway_secret='foo',
    )

    with pytest.raises(RuntimeError) as e:
        provider.process_oauth_response(
            {
                'error': 'foo',
                'error_description': 'bar',
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
        provider.process_oauth_response({
            'code': '0xdeadbeef',
            'oauth_redirect_secret': 'foo'
        })

        assert provider.publishable_key == 'pubkey'
        assert provider.user_id == 'uid'
        assert provider.refresh_token == 'rtoken'
        assert provider.access_token == 'atoken'


def test_stripe_fee_policy() -> None:
    assert StripeFeePolicy.from_amount(100) == 3.2
    assert StripeFeePolicy.compensate(100) == 103.3
    assert StripeFeePolicy.compensate(33.33) == 34.63


def test_stripe_capture_good_charge() -> None:
    class GoodCharge:
        captured = False

        def capture(self) -> None:
            self.captured = True

    charge = GoodCharge()

    with mock.patch('stripe.Charge.retrieve', return_value=charge):
        StripeCaptureManager.capture_charge('foo', 'bar')
        assert not charge.captured

        transaction.commit()
        assert charge.captured


def test_stripe_capture_evil_charge(capturelog: CaptureLogFixture) -> None:
    capturelog.setLevel(logging.ERROR, logger='onegov.pay')

    class EvilCharge:
        def capture(self) -> None:
            raise AssertionError()

    charge = EvilCharge()

    with mock.patch('stripe.Charge.retrieve', return_value=charge):
        StripeCaptureManager.capture_charge('foo', 'bar')

        transaction.commit()
        assert capturelog.records()[0].message == (
            'Stripe charge with capture id bar failed')


def test_stripe_capture_negative_vote() -> None:
    with mock.patch('stripe.Charge.retrieve', side_effect=AssertionError()):
        StripeCaptureManager.capture_charge('foo', 'bar')

        with pytest.raises(AssertionError):
            transaction.commit()


def test_stripe_prepare_oauth_request() -> None:
    stripe = StripeConnect()
    stripe.oauth_gateway = 'https://oauth.example.org'
    stripe.oauth_gateway_auth = 'gateway_auth'
    stripe.oauth_gateway_secret = 'gateway_secret'
    stripe.client_id = 'client_id'
    stripe.client_secret = 'client_secret'

    with requests_mock.Mocker() as m:
        m.post('https://oauth.example.org/register/gateway_auth', json={
            'token': '0xdeadbeef'
        })

        url = stripe.prepare_oauth_request(
            redirect_uri='https://endpoint',
            success_url='https://success',
            error_url='https://error'
        )

        assert quote('https://oauth.example.org/redirect', safe='') in url

        url_obj = URL(url)
        assert url_obj.query_param('state') == '0xdeadbeef'
        assert url_obj.query_param('scope') == 'read_write'
        assert url_obj.query_param('client_id') == 'client_id'
