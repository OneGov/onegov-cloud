from __future__ import annotations

from decimal import Decimal
from onegov.pay.collections import (
    PaymentCollection,
    PaymentProviderCollection,
)
from onegov.pay.errors import (
    CARD_ERRORS,
    DatatransApiError,
    DatatransPaymentError,
    SaferpayApiError,
    SaferpayPaymentError,
)
from onegov.pay.models import Payment, PaymentProvider


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# --- errors -------------------------------------------------------------


def test_datatrans_api_error() -> None:
    error = DatatransApiError('42', 'boom', terminal=True)
    assert error.code == '42'
    assert error.message == 'boom'
    assert error.terminal is True
    assert str(error) == '42: boom'
    assert isinstance(error, DatatransPaymentError)


def test_saferpay_api_error() -> None:
    error = SaferpayApiError(
        'TRANSACTION_DECLINED', 'nope', 'ABORT', detail=['a', 'b']
    )
    assert error.name == 'TRANSACTION_DECLINED'
    assert error.message == 'nope'
    assert error.behavior == 'ABORT'
    assert error.details == ('a', 'b')
    assert 'nope' in str(error)
    assert 'a' in str(error)
    assert isinstance(error, SaferpayPaymentError)

    # an expected, ignorable failure
    assert error.is_expected_failure is True
    assert error.not_started_or_is_expected_failure is True

    # not started also counts as "ok to ignore when cancelling"
    not_started = SaferpayApiError('TRANSACTION_NOT_STARTED', '', 'ABORT')
    assert not_started.is_expected_failure is False
    assert not_started.not_started_or_is_expected_failure is True

    # a genuinely unexpected failure
    unexpected = SaferpayApiError('SOMETHING_ELSE', '', 'ABORT')
    assert unexpected.is_expected_failure is False
    assert unexpected.not_started_or_is_expected_failure is False


def test_card_errors_membership() -> None:
    assert DatatransPaymentError in CARD_ERRORS
    assert SaferpayPaymentError in CARD_ERRORS


# --- payment provider collection ----------------------------------------


def test_payment_provider_collection_crud(session: Session) -> None:
    providers = PaymentProviderCollection(session)
    assert providers.model_class is PaymentProvider

    provider = providers.add()
    assert providers.query().count() == 1

    # sync is a no-op on the generic provider, but must not raise
    providers.sync()
    assert provider.default is False


def test_payment_provider_as_default(session: Session) -> None:
    providers = PaymentProviderCollection(session)
    first = providers.add()
    second = providers.add()

    def default() -> PaymentProvider | None:
        return providers.query().filter_by(default=True).one_or_none()

    providers.as_default(first)
    assert default() is first

    # switching the default resets the previous one
    providers.as_default(second)
    session.flush()
    assert default() is second


# --- payment collection -------------------------------------------------


def test_payment_collection_add_source_default(session: Session) -> None:
    payments = PaymentCollection(session)
    payment = payments.add(amount=Decimal('10'))
    assert payment.source == 'generic'
    assert payment.currency == 'CHF'
    assert payment.state == 'open'


def test_payment_collection_equality(session: Session) -> None:
    assert PaymentCollection(session) == PaymentCollection(session)
    assert PaymentCollection(session) != PaymentCollection(session, page=1)
    assert PaymentCollection(session) != PaymentCollection(
        session, status='paid')
    assert PaymentCollection(session) != object()


def test_payment_collection_by_state(session: Session) -> None:
    provider = PaymentProvider()
    session.add(provider.payment(amount=Decimal('1'), state='open'))
    session.add(provider.payment(amount=Decimal('2'), state='paid'))
    session.flush()

    payments = PaymentCollection(session)
    assert payments.subset().count() == 2

    paid = payments.by_state('paid')
    assert paid.status == 'paid'
    assert paid.subset().count() == 1
    assert paid.subset().one().state == 'paid'


def test_payment_collection_subset_filters(session: Session) -> None:
    provider = PaymentProvider()
    # a provider-backed payment and a manual one (no provider)
    session.add(provider.payment(amount=Decimal('1'), state='open'))
    session.add(Payment(amount=Decimal('2'), state='paid'))
    session.flush()

    payments = PaymentCollection(session)

    assert payments.by_state('open').subset().count() == 1

    provider_only = PaymentCollection(session, payment_type='provider')
    assert provider_only.subset().count() == 1
    assert provider_only.subset().one().provider_id is not None

    manual_only = PaymentCollection(session, payment_type='manual')
    assert manual_only.subset().count() == 1
    assert manual_only.subset().one().provider_id is None


def test_payment_collection_empty_batch_helpers(session: Session) -> None:
    payments = PaymentCollection(session)
    assert payments.tickets_by_batch() == {}
    assert payments.reservation_dates_by_batch() == {}
    assert payments.payment_links_by_batch() is None


def test_payment_collection_page_by_index_preserves_filters(
    session: Session
) -> None:
    payments = PaymentCollection(
        session, source='generic', status='paid', payment_type='manual'
    )
    other = payments.page_by_index(2)
    assert other.page == 2
    assert other.source == 'generic'
    assert other.status == 'paid'
    assert other.payment_type == 'manual'


def test_payment_collection_no_date_filter(session: Session) -> None:
    provider = PaymentProvider()
    session.add(provider.payment(amount=Decimal('1')))
    session.flush()
    payments = PaymentCollection(session, start=None, end=None)
    assert payments.subset().count() == 1
