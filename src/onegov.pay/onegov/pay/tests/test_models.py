import pytest
import transaction

from onegov.core.orm import Base, SessionManager
from onegov.core.orm.types import UUID
from onegov.pay.models import Payable, Payment, PaymentProvider, ManualPayment
from onegov.pay.collections import PaymentCollection
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4
from sqlalchemy.exc import IntegrityError


def test_payment_with_different_bases(postgres_dsn):

    MyBase = declarative_base()

    class Order(MyBase, Payable):
        __tablename__ = 'orders'

        id = Column(UUID, primary_key=True, default=uuid4)
        title = Column(Text)

    class Subscription(Base, Payable):
        __tablename__ = 'subscriptions'

        id = Column(UUID, primary_key=True, default=uuid4)
        title = Column(Text)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(MyBase)
    mgr.set_current_schema('foobar')
    session = mgr.session()

    provider = PaymentProvider()

    apple = Order(title="Apple")
    pizza = Order(title="Pizza")
    kebab = Order(title="Kebab")
    times = Subscription(title="Times")

    apple.payment = provider.payment(amount=100)
    pizza.payment = provider.payment(amount=200)
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

    assert apple.payment.amount == 100
    assert pizza.payment.amount == 200
    assert kebab.payment.amount == 100
    assert times.payment.amount == 200


def test_payment_referential_integrity(postgres_dsn):

    MyBase = declarative_base()

    class Order(MyBase, Payable):
        __tablename__ = 'orders'

        id = Column(UUID, primary_key=True, default=uuid4)
        title = Column(Text)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(MyBase)
    mgr.set_current_schema('foobar')
    session = mgr.session()

    apple = Order(title="Apple", payment=PaymentProvider().payment(amount=100))
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

    assert not list(session.execute("select * from orders"))
    assert not list(session.execute("select * from payments"))
    assert not list(session.execute("select * from payments_for_orders"))

    mgr.dispose()


def test_backref(postgres_dsn):

    MyBase = declarative_base()

    class Product(MyBase, Payable):
        __tablename__ = 'products'

        id = Column(UUID, primary_key=True, default=uuid4)
        title = Column(Text)

    class Part(MyBase, Payable):
        __tablename__ = 'parts'

        id = Column(UUID, primary_key=True, default=uuid4)
        title = Column(Text)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(MyBase)
    mgr.set_current_schema('foobar')
    session = mgr.session()

    provider = PaymentProvider()

    car = Product(title="Car", payment=provider.payment(amount=10000))
    nut = Part(title="Nut", payment=provider.payment(amount=10))
    session.add_all((car, nut))
    session.flush()

    payments = session.query(Payment).all()
    assert [t.title for p in payments for t in p.linked_products] == ["Car"]
    assert [t.title for p in payments for t in p.linked_parts] == ["Nut"]

    assert len(car.payment.linked_products) == 1
    assert len(car.payment.linked_parts) == 0
    assert len(nut.payment.linked_products) == 0
    assert len(nut.payment.linked_parts) == 1

    assert car.payment.links.count() == 1
    assert car.payment.links.first().title == "Car"
    assert nut.payment.links.count() == 1
    assert nut.payment.links.first().title == "Nut"

    assert len(PaymentCollection(session).payment_links_by_batch()) == 2

    session.delete(nut.payment)
    nut.payment = car.payment
    session.flush()

    assert len(car.payment.linked_products) == 1
    assert len(car.payment.linked_parts) == 1
    assert len(nut.payment.linked_products) == 1
    assert len(nut.payment.linked_parts) == 1

    assert car.payment.links.count() == 2
    assert {r.title for r in car.payment.links} == {"Car", "Nut"}

    assert len(PaymentCollection(session).payment_links_by_batch()) == 1

    mgr.dispose()


def test_manual_payment(postgres_dsn):

    MyBase = declarative_base()

    class Product(MyBase, Payable):
        __tablename__ = 'products'

        id = Column(UUID, primary_key=True, default=uuid4)
        title = Column(Text)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(MyBase)
    mgr.set_current_schema('foobar')
    session = mgr.session()

    car = Product(title="Car", payment=ManualPayment(amount=10000))
    session.add(car)
    session.flush()

    payments = session.query(Payment).all()
    assert [t.title for p in payments for t in p.linked_products] == ["Car"]
