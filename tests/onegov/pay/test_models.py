from __future__ import annotations

import pytest
import transaction

from decimal import Decimal
from libres.db.models import ORMBase as LibresORMBase
from onegov.core.orm import Base, SessionManager
from onegov.pay.models import Payable, Payment, PaymentProvider, ManualPayment
from onegov.pay.collections import PaymentCollection
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import mapped_column, registry, DeclarativeBase, Mapped
from uuid import uuid4, UUID


def test_payment_with_different_bases(postgres_dsn: str) -> None:
    class MyBase(DeclarativeBase):
        registry = registry()

    class Order(MyBase, Payable):
        __tablename__ = 'orders'

        id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
        title: Mapped[str | None]

    class Subscription(MyBase, Payable):
        __tablename__ = 'subscriptions'

        id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
        title: Mapped[str | None]

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(MyBase)

    # Explicitly add libres.db.models.ORMBase to the session manager's bases
    # if it was successfully imported. This ensures tables for models on
    # this base (like libres.db.models.Reservation) are created.
    if LibresORMBase not in mgr.bases:
        mgr.bases.append(LibresORMBase)
    mgr.set_current_schema('foobar')
    session = mgr.session()

    provider = PaymentProvider()

    apple = Order(title="Apple")
    pizza = Order(title="Pizza")
    kebab = Order(title="Kebab")
    times = Subscription(title="Times")

    apple.payment = provider.payment(amount=Decimal(100))
    pizza.payment = provider.payment(amount=Decimal(200))
    kebab.payment = apple.payment
    times.payment = pizza.payment

    session.add_all((apple, pizza, kebab, times))
    session.flush()

    assert session.query(Payment).count() == 2
    assert session.query(Order).count() == 3
    assert session.query(Subscription).count() == 1

    apple = session.query(Order).filter_by(title="Apple").one()
    pizza = session.query(Order).filter_by(title="Pizza").one()
    kebab = session.query(Order).filter_by(title="Kebab").one()
    times = session.query(Subscription).filter_by(title="Times").one()

    assert apple.payment is not None
    assert apple.payment.amount == 100
    assert pizza.payment is not None
    assert pizza.payment.amount == 200
    assert kebab.payment is not None
    assert kebab.payment.amount == 100
    assert times.payment is not None
    assert times.payment.amount == 200

    mgr.dispose()


def test_payment_referential_integrity(postgres_dsn: str) -> None:
    class MyBase(DeclarativeBase):
        registry = registry()

    class Order(MyBase, Payable):
        __tablename__ = 'orders'

        id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
        title: Mapped[str | None]

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(MyBase)

    # Explicitly add libres.db.models.ORMBase to the session manager's bases
    # if it was successfully imported. This ensures tables for models on
    # this base (like libres.db.models.Reservation) are created.
    if LibresORMBase not in mgr.bases:
        mgr.bases.append(LibresORMBase)
    mgr.set_current_schema('foobar')
    session = mgr.session()

    apple = Order(
        title="Apple",
        payment=PaymentProvider().payment(amount=Decimal(100))
    )
    session.add(apple)
    transaction.commit()

    with pytest.raises(IntegrityError):
        session.delete(session.query(PaymentProvider).one())
        session.flush()

    transaction.abort()

    # as a precaution we only allow deletion of elements after the payment
    # has been explicitly deleted
    with pytest.raises(IntegrityError):
        session.delete(session.query(Order).one())
        session.flush()

    transaction.abort()

    with pytest.raises(IntegrityError):
        session.delete(session.query(Order).one())
        session.delete(session.query(Payment).one())
        session.flush()

    transaction.abort()

    session.delete(session.query(Payment).one())
    session.delete(session.query(Order).one())
    transaction.commit()

    assert not list(session.execute(text("select * from orders")))
    assert not list(session.execute(text("select * from payments")))
    assert not list(session.execute(text(
        "select * from payments_for_orders_payment"
    )))

    mgr.dispose()


def test_backref(postgres_dsn: str) -> None:
    class MyBase(DeclarativeBase):
        registry = registry()

    class Product(MyBase, Payable):
        __tablename__ = 'products'

        id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
        title: Mapped[str | None]

    class Part(MyBase, Payable):
        __tablename__ = 'parts'

        id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
        title: Mapped[str | None]

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(MyBase)

    # Explicitly add libres.db.models.ORMBase to the session manager's bases
    # if it was successfully imported. This ensures tables for models on
    # this base (like libres.db.models.Reservation) are created.
    if LibresORMBase not in mgr.bases:
        mgr.bases.append(LibresORMBase)
    mgr.set_current_schema('foobar')
    session = mgr.session()

    provider = PaymentProvider()

    car = Product(title="Car", payment=provider.payment(amount=Decimal(10000)))
    nut = Part(title="Nut", payment=provider.payment(amount=Decimal(10)))
    session.add_all((car, nut))
    session.flush()

    payments = session.query(Payment).all()
    assert [t.title for p in payments for t in p.linked_products] == ["Car"]  # type: ignore[attr-defined]
    assert [t.title for p in payments for t in p.linked_parts] == ["Nut"]  # type: ignore[attr-defined]

    assert car.payment is not None
    assert nut.payment is not None
    assert len(car.payment.linked_products) == 1  # type: ignore[attr-defined]
    assert len(car.payment.linked_parts) == 0  # type: ignore[attr-defined]
    assert len(nut.payment.linked_products) == 0  # type: ignore[attr-defined]
    assert len(nut.payment.linked_parts) == 1  # type: ignore[attr-defined]

    assert car.payment.links.count() == 1
    assert car.payment.links.first().title == "Car"  # type: ignore[union-attr]
    assert nut.payment.links.count() == 1
    assert nut.payment.links.first().title == "Nut"  # type: ignore[union-attr]

    assert len(PaymentCollection(session).payment_links_by_batch()) == 2  # type: ignore[arg-type]

    session.delete(nut.payment)
    nut.payment = car.payment
    session.flush()

    assert len(car.payment.linked_products) == 1  # type: ignore[attr-defined]
    assert len(car.payment.linked_parts) == 1  # type: ignore[attr-defined]
    assert len(nut.payment.linked_products) == 1
    assert len(nut.payment.linked_parts) == 1

    assert car.payment.links.count() == 2
    assert {r.title for r in car.payment.links} == {"Car", "Nut"}  # type: ignore[attr-defined]

    assert len(PaymentCollection(session).payment_links_by_batch()) == 1  # type: ignore[arg-type]

    mgr.dispose()


def test_manual_payment(postgres_dsn: str) -> None:
    class MyBase(DeclarativeBase):
        registry = registry()

    class Product(MyBase, Payable):
        __tablename__ = 'products'

        id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
        title: Mapped[str | None]

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(MyBase)

    # Explicitly add libres.db.models.ORMBase to the session manager's bases
    # if it was successfully imported. This ensures tables for models on
    # this base (like libres.db.models.Reservation) are created.
    if LibresORMBase not in mgr.bases:
        mgr.bases.append(LibresORMBase)
    mgr.set_current_schema('foobar')
    session = mgr.session()

    car = Product(title="Car", payment=ManualPayment(amount=Decimal(10000)))
    session.add(car)
    session.flush()

    payments = session.query(Payment).all()
    assert [t.title for p in payments for t in p.linked_products] == ["Car"]  # type: ignore[attr-defined]

    mgr.dispose()
