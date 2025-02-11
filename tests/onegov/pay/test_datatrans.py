import pytest
import transaction

from onegov.pay.models.payment_providers.datatrans import (
    DatatransFeePolicy,
    DatatransProvider,
    DatatransSettleManager,
    DatatransTransaction,
)
from unittest import mock


@pytest.fixture(autouse=True)
def no_requests(monkeypatch):
    # prevents tests from making live requests
    mock_session = mock.Mock()
    monkeypatch.delattr('requests.sessions.Session.request')


def test_datatrans_fee_policy():
    assert DatatransFeePolicy.from_amount(100) == .29
    assert DatatransFeePolicy.compensate(100) == 100.29


def test_datatrans_settle_good_tx():
    mock_session = mock.Mock()
    provider = DatatransProvider(merchant_id='foo')
    client = provider.client
    client.session = mock_session
    tx = DatatransTransaction(
        merchantId='foo',
        transactionId='bar',
        type='payment',
        status='authorized',
        refno='baz',
        currency='CHF',
        detail={'authorize': {'amount': 100}}
    )

    with mock.patch(
        'onegov.pay.models.payment_providers.datatrans.DatatransClient.status',
        return_value=tx
    ):
        DatatransSettleManager.settle_charge(client, tx)
        mock_session.post.assert_not_called()

        transaction.commit()
        mock_session.post.assert_called_once_with(
            f'{client.base_url}/transactions/bar/settle',
            json={'amount': 100, 'currency': 'CHF', 'refno': 'baz'}
        )


def test_datatrans_settle_bad_tx(caplog):
    mock_session = mock.Mock()
    provider = DatatransProvider(merchant_id='foo')
    client = provider.client
    client.session = mock_session
    tx = DatatransTransaction(
        merchantId='foo',
        transactionId='bar',
        type='payment',
        status='authorized',
        refno='baz',
        currency='CHF',
        detail={'authorize': {'amount': 100}}
    )

    with mock.patch(
        'onegov.pay.models.payment_providers.datatrans.DatatransClient.status',
        return_value=tx
    ), mock.patch(
        'onegov.pay.models.payment_providers.datatrans.DatatransClient.settle',
        side_effect=AssertionError('settle failed')
    ):
        DatatransSettleManager.settle_charge(client, tx)

        transaction.commit()
        assert 'settle failed' in caplog.text


def test_datatrans_settle_negative_vote():
    mock_session = mock.Mock()
    provider = DatatransProvider(merchant_id='foo')
    client = provider.client
    client.session = mock_session
    tx = DatatransTransaction(
        merchantId='not_foo',
        transactionId='bar',
        type='payment',
        status='authorized',
        refno='baz',
        currency='CHF',
        detail={'authorize': {'amount': 100}}
    )

    with mock.patch(
        'onegov.pay.models.payment_providers.datatrans.DatatransClient.status',
        return_value=tx
    ):
        DatatransSettleManager.settle_charge(client, tx)

        with pytest.raises(AssertionError):
            transaction.commit()

        mock_session.post.assert_not_called()
