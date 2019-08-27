from onegov.core.orm import Base
from onegov.core.orm import SessionManager
from onegov.core.orm.types import UUID
from onegov.pay import Payable, PayableCollection
from onegov.pay import PaymentCollection
from onegov.pay import PaymentProvider
from sqlalchemy import Column
from sqlalchemy import Text
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4


def test_payment_collection_pagination(session):
    provider = PaymentProvider()

    session.add_all(
        provider.payment(amount=amount)
        for amount in range(100, 2000, 100)
    )

    payments = PaymentCollection(session)
    assert payments.query().count() == 19

    assert len(payments.batch) == 10
    assert len(payments.page_by_index(1).batch) == 9


def test_payment_collection_crud(session):
    payments = PaymentCollection(session)
    payment = payments.add(amount=100, provider=PaymentProvider())

    assert payment.amount == 100
    assert payments.query().count() == 1

    payments.delete(payment)
    assert payments.query().count() == 0


def test_payable_collection(postgres_dsn):

    MyBase = declarative_base()

    class Order(MyBase, Payable):
        __tablename__ = 'orders'

        id = Column(UUID, primary_key=True, default=uuid4)
        title = Column(Text)

    class Newspaper(MyBase, Payable):
        __tablename__ = 'newspapers'

        id = Column(UUID, primary_key=True, default=uuid4)
        title = Column(Text)

    mgr = SessionManager(postgres_dsn, Base)
    mgr.bases.append(MyBase)
    mgr.set_current_schema('foobar')
    session = mgr.session()

    provider = PaymentProvider()

    carbonara = Order(title="Carbonara")
    coca_cola = Order(title="Coca Cola")

    the_wapo = Newspaper(title="The Washington Post")
    ny_times = Newspaper(title="The New York Times")

    carbonara.payment = coca_cola.payment = provider.payment(amount=25)
    the_wapo.payment = provider.payment(amount=4.50)
    ny_times.payment = provider.payment(amount=5.50)

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
