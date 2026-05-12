from __future__ import annotations

import pytest
import transaction

from datetime import datetime
from onegov.pay.errors import SaferpayPaymentError
from onegov.pay.models.payment_providers.worldline_saferpay import (
    SaferpayCaptureManager,
    SaferpayTransaction,
    WorldlineFeePolicy,
    WorldlineSaferpay,
)
from unittest import mock


@pytest.fixture(autouse=True)
def no_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    # prevents tests from making live requests
    mock_session = mock.Mock()
    monkeypatch.delattr('requests.sessions.Session.request')


def test_worldline_fee_policy() -> None:
    assert WorldlineFeePolicy.from_amount(100) == 1.89
    assert WorldlineFeePolicy.compensate(100) == 101.92
    assert WorldlineFeePolicy.compensate(33.33) == 34.1


def test_saferpay_capture_good_tx() -> None:
    mock_session = mock.Mock()
    provider = WorldlineSaferpay(customer_id='foo', terminal_id='bar')
    client = provider.client
    client.session = mock_session
    tx = SaferpayTransaction(
        id='baz',
        date=datetime.now(),
        six_transaction_reference='six',
        type='PAYMENT',
        status='AUTHORIZED',
        amount={'value': '100', 'currency_code': 'CHF'},  # type: ignore[arg-type]
    )

    with mock.patch(
        'onegov.pay.models.payment_providers'
        '.worldline_saferpay.SaferpayClient.inquire',
        return_value=tx
    ):
        SaferpayCaptureManager.capture_charge(client, tx)
        mock_session.post.assert_not_called()

        transaction.commit()
        mock_session.post.assert_called_once()


def test_datatrans_settle_bad_tx(caplog: pytest.LogCaptureFixture) -> None:
    mock_session = mock.Mock()
    provider = WorldlineSaferpay(customer_id='foo', terminal_id='bar')
    client = provider.client
    client.session = mock_session
    tx = SaferpayTransaction(
        id='baz',
        date=datetime.now(),
        six_transaction_reference='six',
        type='PAYMENT',
        status='AUTHORIZED',
        amount={'value': '100', 'currency_code': 'CHF'},  # type: ignore[arg-type]
    )

    with mock.patch(
        'onegov.pay.models.payment_providers'
        '.worldline_saferpay.SaferpayClient.inquire',
        return_value=tx
    ), mock.patch(
        'onegov.pay.models.payment_providers'
        '.worldline_saferpay.SaferpayClient.capture',
        side_effect=AssertionError('capture failed')
    ):
        SaferpayCaptureManager.capture_charge(client, tx)

        transaction.commit()
        assert 'capture failed' in caplog.text


def test_datatrans_settle_negative_vote() -> None:
    mock_session = mock.Mock()
    provider = WorldlineSaferpay(customer_id='foo', terminal_id='bar')
    client = provider.client
    client.session = mock_session
    tx = SaferpayTransaction(
        id='baz',
        date=datetime.now(),
        six_transaction_reference='six',
        type='REFUND',
        status='AUTHORIZED',
        amount={'value': '100', 'currency_code': 'CHF'},  # type: ignore[arg-type]
    )

    with mock.patch(
        'onegov.pay.models.payment_providers'
        '.worldline_saferpay.SaferpayClient.inquire',
        return_value=tx
    ):
        SaferpayCaptureManager.capture_charge(client, tx)

        with pytest.raises(SaferpayPaymentError):
            transaction.commit()

        mock_session.post.assert_not_called()
