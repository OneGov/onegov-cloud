from onegov.pay.models.payment import Payment
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship


class Payable(object):
    """ Links the parent model with 0-n :class:`~onegov.pay.models.Payment`
    records through an automatically generated association table.

    """

    @declared_attr
    def payment(cls):
        name = 'payments_for_{}'.format(cls.__tablename__)
        key = '{}_id'.format(cls.__tablename__)
        target = '{}.id'.format(cls.__tablename__)
        backref = 'linked_{}'.format(cls.__tablename__)

        payment_association = Table(
            name,
            cls.metadata,
            Column(key, ForeignKey(target), primary_key=True, nullable=False),
            Column('payment_id', ForeignKey(Payment.id), nullable=False))

        Payment.register_link(backref, cls, payment_association, key)

        return relationship(
            argument=Payment,
            secondary=payment_association,
            backref=backref,
            cascade=False,
            uselist=False,
            passive_deletes=True)
