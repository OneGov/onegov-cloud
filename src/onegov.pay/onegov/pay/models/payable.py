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
        tablename = 'payments_for_{}'.format(cls.__tablename__)
        key_name = '{}_id'.format(cls.__tablename__)
        target_column = '{}.id'.format(cls.__tablename__)

        payment_association = Table(
            tablename,
            cls.metadata,
            Column(
                key_name, ForeignKey(target_column),
                primary_key=True,
                nullable=False
            ),
            Column(
                'payment_id', ForeignKey(Payment.id),
                nullable=False
            ))

        Payment.register_link(cls)

        return relationship(
            argument=Payment,
            secondary=payment_association,
            uselist=False,
            backref='linked_{}'.format(cls.__tablename__),
            cascade=False,
            passive_deletes=True)
