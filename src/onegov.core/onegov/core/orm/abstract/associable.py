""" Generic associations are an interesting SQLAlchemy design pattern
that allow for collections of records to be attached to other models by
mere inheritance.

Generic associations are useful in situations where a model should be
attachable to a number of third-party models. For example, we might say that
a comment model should be attacheable to any other model (say a page or a
ticket). In such an instance generic associations offer the benefit of
being simple to integrate on the third-party model.

Additionally we can define generic methods that work on all third-party
models that inherit from the associated model (in our example imagine a
"Commentable" class that leads to the automatic attachment of comments to
Page/Ticket models).

See also:
https://github.com/zzzeek/sqlalchemy/blob/master/examples/
generic_associations/table_per_association.py

Note that you do not want to use these associations in lieue of simple
relationships between two models. The standard way of doing this leads to a
strong relationship on the database and is easier to change and reason about.

Generic associations are meant for generic usecases. These currently include
payments (any model may be payable) and files (any model may have files
attached). Other generic associations should be introduced along these
lines.

A single model may be associated to any number of other models. For example::

                            ┌─────────────┐
                      ┌─────│ Reservation │
    ┌────────────┐    │     └─────────────┘
    │  Payment   │◀───┤
    └────────────┘    │     ┌─────────────┐
                      └─────│    Form     │
                            └─────────────┘

Here, ``Payment`` is associable (through the ``Payable`` mixin).
``Reservation`` and ``Form`` in turn inherit from ``Payable``.

This all is probably best understood in an example:

        class Payment(Base, Associable):
            __tablename__ == 'payments'

        class Payable(object):
            payment = associated(Payment, 'payment', 'one-to-one')

        class Product(Base, Payable):
            __tablename__ == 'products'

This results in a product model which has a payment attribute attached to it.
The payments are stored in the ``payments`` table, products in the ``products``
table. The link between the two is established in the automatically created
``payments_for_products`` table.

"""

from collections import namedtuple
from onegov.core.orm.utils import QueryChain
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import object_session
from sqlalchemy.orm import backref, relationship


class RegisteredLink(namedtuple("RegisteredLink", (
    'cls',
    'table',
    'key',
    'attribute',
    'cardinality',
))):

    @property
    def class_attribute(self):
        return getattr(self.cls, self.attribute)


def associated(associated_cls, attribute_name, cardinality='one-to-many',
               uselist='auto'):
    """ Creates an associated attribute. This attribute is supposed to be
    defined on the mixin class that will establish the generic association
    if inherited by a model.

    :param associated_cls:
        The class which the model will be associated with.

    :param attribute_name:
        The name of the attribute used on the mixin class.

    :param cardinality:
        May be 'one-to-one', 'one-to-many' or 'many-to-many'. Cascades are
        used automatically, unless 'many-to-many' is used, in which case
        cascades are disabled.

    :param uselist:
        True if the attribute on the inheriting model is a list. Use 'auto'
        if this should be automatically decided depending on the cardinality.

    Example::

        class Adress(Base, Associable):
            pass

        class Addressable(object):
            address = associated(Address, 'address', 'one-to-one')

        class Company(Base, Addressable):
            pass

    """

    assert cardinality in ('one-to-one', 'one-to-many', 'many-to-many')

    if cardinality in ('one-to-one', 'one-to-many'):
        cascade = 'all, delete-orphan'
        single_parent = True
        passive_deletes = False
    else:
        cascade = False
        single_parent = False
        passive_deletes = True

    if uselist == 'auto':
        uselist = not cardinality.endswith('to-one')

    def descriptor(cls):
        name = '{}_for_{}_{}'.format(
            associated_cls.__tablename__,
            cls.__tablename__,
            attribute_name
        )
        key = '{}_id'.format(cls.__tablename__)
        target = '{}.id'.format(cls.__tablename__)
        backref_name = 'linked_{}'.format(cls.__tablename__)

        association_key = associated_cls.__name__.lower() + '_id'
        association_id = associated_cls.id

        association = Table(
            name, cls.metadata,
            Column(key, ForeignKey(target), nullable=False),
            Column(association_key, ForeignKey(association_id), nullable=False)
        )

        assert issubclass(associated_cls, Associable)

        associated_cls.register_link(
            backref_name, cls, association, key, attribute_name, cardinality)

        return relationship(
            argument=associated_cls,
            secondary=association,
            # The reference from the files class back to the target class fails
            # to account for polymorphic identities.
            #
            # I think this cannot be fixed, as the file class would have to
            # keep track of the polymorphic class in question through a
            # separate column and a loading strategy that takes that into
            # account.
            #
            # As a result we disable type-checks here. Note that the target
            # class may have to override __eq__ and __hash__ to get cascades
            # to work properly.
            #
            # Have a look at onegov.chat.models.Message to see how that has
            # been done.
            backref=backref(
                backref_name,
                enable_typechecks=False
            ),
            single_parent=single_parent,
            cascade=cascade,
            uselist=uselist,
            passive_deletes=passive_deletes
        )

    return declared_attr(descriptor)


class Associable(object):
    """ Mixin to enable associations on a model. Only models which are
    associable may be targeted by :func:`associated`_

    """

    registered_links = None

    @classmethod
    def association_base(cls):
        """ Returns the model which directly inherits from Associable. """

        for parent in cls.__bases__:
            if parent is Associable:
                return cls
            if issubclass(parent, Associable):
                return parent.association_base()

        return cls

    @classmethod
    def register_link(cls, link_name, linked_class, table, key,
                      attribute, cardinality):
        """ All associated classes are registered through this method. This
        yields the following benefits:

        1. We gain the ability to query all the linked records in one query.
           This is hard otherwise as each ``Payable`` class leads to its own
           association table which needs to be queried separately.

        2. We are able to reset all created backreferences. This is necessary
           during tests. SQLAlchemy keeps these references around and won't
           let us re-register the same model multiple times (which outside
           of tests is completely reasonable).

        """
        base = cls.association_base()

        if not base.registered_links:
            base.registered_links = {}

        base.registered_links[link_name] = RegisteredLink(
            cls=linked_class,
            table=table,
            key=key,
            attribute=attribute,
            cardinality=cardinality
        )

    @property
    def links(self):
        """ Returns a query chain with all records of all models which attach
        to the associable model.

        """

        session = object_session(self)

        def query(link):
            column = getattr(link.cls, link.attribute)

            q = session.query(link.cls)

            if column.property.uselist:
                q = q.filter(column.contains(self))
            else:
                q = q.filter(column == self)

            return q.options(joinedload(column))

        return QueryChain(tuple(
            query(link) for link in self.registered_links.values()
        ))
