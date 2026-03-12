from __future__ import annotations

from onegov.org.models.document_form import FormDocument
from onegov.page import Page
from onegov.form import FormDefinition
from onegov.reservation import Resource


from typing import Any, Generic, TypeVar, TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.orm.abstract import MoveDirection
    from onegov.org.models import (  # noqa: F401
        BuiltinFormDefinition, CustomFormDefinition, News, Topic)
    from onegov.org.models.extensions import PersonLinkExtension
    from onegov.org.models.resource import (  # noqa: F401
        DaypassResource, ItemResource, RoomResource)
    from sqlalchemy.orm import Session
    from uuid import UUID


_OwnerT = TypeVar('_OwnerT', bound='PersonLinkExtension')


class PersonMove(Generic[_OwnerT]):
    """ Represents a single move of a linked person. """

    def __init__(
        self,
        session: Session,
        obj: _OwnerT,
        subject: str,
        target: str,
        direction: MoveDirection
    ) -> None:

        self.session = session
        self.obj = obj

        # remove the dashes from the uuid
        self.subject = subject.replace('-', '')
        self.target = target.replace('-', '')
        self.direction = direction

    def execute(self) -> None:
        self.obj.move_person(
            subject=self.subject,
            target=self.target,
            direction=self.direction
        )

    @staticmethod
    def get_implementation(
        obj: object
    ) -> type[PagePersonMove | FormPersonMove | ResourcePersonMove]:
        # XXX this is not really extendable by other org applications. They
        # need to override this function *and* define new paths for each class
        # they add.
        #
        # To simplify we should create a registry using dectate, which handles
        # the classes for us. We'd only have one path and the PersonMove
        # class would gain a 'type' and a generic 'key' property which we would
        # use to lookup the actual handler for the move.
        #
        # For example:
        #
        # @App.person_move_handler()
        # class PagePersonMoveMapping:
        #     def get_object(self, key):
        #        ...
        #     def get_key(self, obj):
        #        ...
        #
        if isinstance(obj, Page):
            return PagePersonMove

        if isinstance(obj, FormDefinition | FormDocument):
            return FormPersonMove

        if isinstance(obj, Resource):
            return ResourcePersonMove

        raise NotImplementedError

    @staticmethod
    def get_key(obj: object) -> Any:
        if isinstance(obj, FormDefinition):
            return obj.name

        assert hasattr(obj, 'id')
        return obj.id


# FIXME: For all of these we would prefer `Page & PersonLinkExtension`
#        but type intersections don't exist yet


class PagePersonMove(PersonMove['News | Topic']):
    """ Represents a single move of a linked person on a page. """

    @property
    def key(self) -> int:
        return self.obj.id


class FormPersonMove(PersonMove[
    'BuiltinFormDefinition | CustomFormDefinition | FormDocument'
]):
    """ Represents a single move of a linked person on a form definition. """

    @property
    def key(self) -> str:
        return self.obj.name


class ResourcePersonMove(PersonMove[
    'DaypassResource | ItemResource | RoomResource'
]):
    """ Represents a single move of a linked person on a form definition. """

    @property
    def key(self) -> UUID:
        return self.obj.id
