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

This all is probably best understood in an example::

        class Payment(Base, Associable):
            __tablename__ == 'payments'

        class Payable:
            payment = associated(Payment, 'payment', 'one-to-one')

        class Product(Base, Payable):
            __tablename__ == 'products'

This results in a product model which has a payment attribute attached to it.
The payments are stored in the ``payments`` table, products in the ``products``
table. The link between the two is established in the automatically created
``payments_for_products`` table.

"""
from __future__ import annotations

from onegov.core.orm.utils import QueryChain
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import UniqueConstraint
from sqlalchemy import Table
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import object_session
from sqlalchemy.orm import backref, relationship, Mapped


from typing import overload, Any, Literal, NamedTuple, TypeVar
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Query
    from .. import Base

    Cardinality = Literal['one-to-many', 'one-to-one', 'many-to-many']


_M = TypeVar('_M', bound='Associable')


class RegisteredLink(NamedTuple):
    cls: type[Base]
    table: Table
    key: str
    attribute: str
    cardinality: Cardinality

    @property
    def class_attribute(self) -> Any:
        return getattr(self.cls, self.attribute)


@overload
def associated(
    associated_cls: type[_M],
    attribute_name: str,
    cardinality: Literal['one-to-many', 'many-to-many'] = ...,
    *,
    uselist: Literal['auto'] = ...,
    backref_suffix: str = ...,
    onupdate: str | None = ...,
    order_by: str | Literal[False] = ...
) -> declared_attr[list[_M]]: ...


@overload
def associated(
    associated_cls: type[_M],
    attribute_name: str,
    cardinality: Literal['one-to-one'],
    *,
    uselist: Literal['auto'] = ...,
    backref_suffix: str = ...,
    onupdate: str | None = ...,
    order_by: str | Literal[False] = ...
) -> declared_attr[_M | None]: ...


@overload
def associated(
    associated_cls: type[_M],
    attribute_name: str,
    cardinality: Cardinality = ...,
    *,
    uselist: Literal[True],
    backref_suffix: str = ...,
    onupdate: str | None = ...,
    order_by: str | Literal[False] = ...
) -> declared_attr[list[_M]]: ...


@overload
def associated(
    associated_cls: type[_M],
    attribute_name: str,
    cardinality: Cardinality = ...,
    *,
    uselist: Literal[False],
    backref_suffix: str = ...,
    onupdate: str | None = ...,
    order_by: str | Literal[False] = ...
) -> declared_attr[_M | None]: ...


def associated(
    associated_cls: type[_M],
    attribute_name: str,
    cardinality: Cardinality = 'one-to-many',
    uselist: Literal['auto'] | bool = 'auto',
    backref_suffix: str = '__tablename__',
    onupdate: str | None = None,
    order_by: str | Literal[False] = False
) -> declared_attr[Any]:
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

    :param backref_suffix:
        Individual suffix used for the backref.

    :param onupdate:
        The 'onupdate' constraint of the foreign key column.

    Example::

        class Adress(Base, Associable):
            pass

        class Addressable:
            address = associated(Address, 'address', 'one-to-one')

        class Company(Base, Addressable):
            pass

    """

    assert cardinality in ('one-to-one', 'one-to-many', 'many-to-many')

    cascade: str
    if cardinality in ('one-to-one', 'one-to-many'):
        cascade = 'all, delete-orphan'
        single_parent = True
        passive_deletes = False
    else:
        # NOTE: This is the default cascade
        cascade = 'save-update, merge'
        single_parent = False
        passive_deletes = True

    if uselist == 'auto':
        uselist = not cardinality.endswith('to-one')

    def descriptor(cls: type[Base]) -> Mapped[list[_M]] | Mapped[_M | None]:
        # HACK: forms is one of the only tables which doesn't use id as
        #       its primary key, we probably should just use id everywhere
        #       consistently
        if cls.__tablename__ == 'forms':
            pk_name = 'name'
        else:
            pk_name = 'id'

        name = '{}_for_{}_{}'.format(
            associated_cls.__tablename__,
            cls.__tablename__,
            attribute_name
        )
        key = f'{cls.__tablename__}_{pk_name}'
        target = f'{cls.__tablename__}.{pk_name}'

        if backref_suffix == '__tablename__':
            backref_name = f'linked_{cls.__tablename__}'
        else:
            backref_name = f'linked_{backref_suffix}'

        association_key = associated_cls.__name__.lower() + '_id'
        association_id = associated_cls.id

        # to be more flexible about polymorphism and where the mixin
        # has to get inserted we only create a new instance for the
        # association table, if we haven't already created it, we
        # also only need to create the backref once, since we punt
        # on polymorphism anyways, but in the case were we don't create
        # a backref we need to set back_populates so introspection
        # is aware that the two relationships are inverses of one
        # another, otherwise things like @observes won't work.
        association_table = cls.metadata.tables.get(name)
        if association_table is None:
            association_table = Table(
                name,
                cls.metadata,
                Column(
                    key,
                    ForeignKey(target, onupdate=onupdate),
                    nullable=False
                ),
                Column(
                    association_key,
                    ForeignKey(association_id),
                    nullable=False
                ),
                UniqueConstraint(
                    key,
                    association_key,
                    name=f'uq_assoc_{name}'
                )
            )
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
            file_backref = backref(
                backref_name,
                enable_typechecks=False
            )
            back_populates = None
        else:
            file_backref = None
            back_populates = backref_name

        assert issubclass(associated_cls, Associable)

        associated_cls.register_link(
            backref_name,
            cls,
            association_table,
            key,
            attribute_name,
            cardinality
        )

        return relationship(
            argument=associated_cls,
            secondary=association_table,
            backref=file_backref,
            back_populates=back_populates,
            single_parent=single_parent,
            cascade=cascade,
            uselist=uselist,
            passive_deletes=passive_deletes,
            order_by=order_by
        )

    # NOTE: We manually set the  return type on __annotations__ so
    #       that SQLAlchemy can actually understand what it means
    if not TYPE_CHECKING:
        descriptor.__annotations__['return'] = Mapped[
            list[associated_cls] if uselist else associated_cls
        ]

    return declared_attr(descriptor)


class Associable:
    """ Mixin to enable associations on a model. Only models which are
    associable may be targeted by :func:`associated`.

    """

    registered_links: dict[str, RegisteredLink] | None = None

    if TYPE_CHECKING:
        # FIXME: This should probably be abstract in some way so that
        #        we can enforce that the class that is Associable has
        #        an id column...
        id: Mapped[Any]

        # HACK: let mypy know that this will have a __tablename__ set
        __tablename__: str

    @classmethod
    def association_base(cls) -> type[Associable]:
        """ Returns the model which directly inherits from Associable. """

        for parent in cls.__bases__:
            if parent is Associable:
                return cls
            if issubclass(parent, Associable):
                return parent.association_base()

        return cls

    @classmethod
    def register_link(
        cls,
        link_name: str,
        linked_class: type[Base],
        table: Table,
        key: str,
        attribute: str,
        cardinality: Cardinality
    ) -> None:
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
    def links(self) -> QueryChain[Base]:
        """ Returns a query chain with all records of all models which attach
        to the associable model.

        """
        assert self.registered_links is not None, 'No links registered'

        session = object_session(self)
        assert session is not None

        def query(link: RegisteredLink) -> Query[Base]:
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
