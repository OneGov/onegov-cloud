from __future__ import annotations

import pytest

from decimal import Decimal
from onegov.core.orm import Base, SessionManager
from onegov.pay import Payable, PayableCollection
from onegov.pay import PaymentCollection
from onegov.pay import PaymentProvider
from sqlalchemy.orm import mapped_column, registry, DeclarativeBase, Mapped
from uuid import uuid4, UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def test_payment_collection_pagination(session: Session) -> None:
    provider = PaymentProvider()

    session.add_all(
        provider.payment(amount=Decimal(amount))
        for amount in range(100, 2000, 20)
    )

    payments = PaymentCollection(session)
    assert payments.query().count() == 95

    assert len(payments.batch) == 50
    assert len(payments.page_by_index(1).batch) == 45


def test_payment_pagination_negative_page_index(session: Session) -> None:
    payments = PaymentCollection(session, page=-1)
    assert payments.page == 0
    assert payments.page_index == 0
    assert payments.page_by_index(-2).page == 0
    assert payments.page_by_index(-3).page_index == 0

    with pytest.raises(AssertionError):
        PaymentCollection(session, page=None)  # type: ignore[arg-type]


def test_payment_collection_crud(session: Session) -> None:
    payments = PaymentCollection(session)
    payment = payments.add(amount=Decimal('100'), provider=PaymentProvider())

    assert payment.amount == Decimal('100')
    assert payments.query().count() == 1

    payments.delete(payment)
    assert payments.query().count() == 0


def test_payable_collection(postgres_dsn: str) -> None:
    class MyBase(DeclarativeBase):
        registry = registry()

    class Order(MyBase, Payable):
        __tablename__ = 'orders'

        id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
        title: Mapped[str | None]

    class Newspaper(MyBase, Payable):
        __tablename__ = 'newspapers'

        id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
        title: Mapped[str | None]

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(MyBase)
    mgr.set_current_schema('foobar')
    session = mgr.session()

    provider = PaymentProvider()

    carbonara = Order(title="Carbonara")
    coca_cola = Order(title="Coca Cola")

    the_wapo = Newspaper(title="The Washington Post")
    ny_times = Newspaper(title="The New York Times")

    carbonara.payment = coca_cola.payment = provider.payment(
        amount=Decimal(25)
    )
    the_wapo.payment = provider.payment(amount=Decimal(4.50))
    ny_times.payment = provider.payment(amount=Decimal(5.50))

    session.add_all((carbonara, coca_cola, the_wapo, ny_times))
    session.flush()

    payables = PayableCollection(session)
    payables.batch_size = 3

    assert payables.query().count() == 4
    assert len(payables.batch) == 3

    payables = payables.page_by_index(1)
    payables.batch_size = 3
    assert len(payables.batch) == 1

    orders = PayableCollection(session, cls=Order)
    assert orders.query().count() == 2
