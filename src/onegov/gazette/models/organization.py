from __future__ import annotations

from onegov.core.orm.abstract import AdjacencyList
from onegov.core.orm.abstract import MoveDirection
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import dict_property
from onegov.core.orm.mixins import meta_property
from onegov.core.orm.mixins import TimestampMixin
from onegov.gazette.observer import observes
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import or_
from sqlalchemy.orm import object_session


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterator
    from collections.abc import Sequence
    from onegov.gazette.models.notice import GazetteNotice
    from sqlalchemy.orm import Query
    from sqlalchemy.orm import Session
    from sqlalchemy.orm import relationship


class Organization(AdjacencyList, ContentMixin, TimestampMixin):

    """ Defines an organization for official notices.

    Although the categories are defined as a flexible adjacency list, we
    currently use it only as a two-stage adjacency list key-value list
    (name-title).

    """

    __tablename__ = 'gazette_organizations'

    #: True, if this organization is still in use.
    active: Column[bool | None] = Column(Boolean, nullable=True)

    external_name: dict_property[str | None] = meta_property('external_name')

    if TYPE_CHECKING:
        # we need to override these attributes to get the correct base class
        parent: relationship[Organization | None]
        children: relationship[Sequence[Organization]]

        @property
        def root(self) -> Organization: ...
        @property
        def ancestors(self) -> Iterator[Organization]: ...

    def notices(self) -> Query[GazetteNotice]:
        """ Returns a query to get all notices related to this category. """

        from onegov.gazette.models.notice import GazetteNotice  # circular

        notices = object_session(self).query(GazetteNotice)
        notices = notices.filter(
            GazetteNotice._organizations.has_key(self.name)  # type:ignore
        )

        return notices

    @property
    def in_use(self) -> bool:
        """ True, if the organization is used by any notice. """

        session = object_session(self)
        return session.query(self.notices().exists()).scalar()

    @observes('title')
    def title_observer(self, title: str) -> None:
        from onegov.gazette.models.notice import GazetteNotice  # circular

        notices = self.notices()
        notices = notices.filter(
            or_(
                GazetteNotice.organization.is_(None),
                GazetteNotice.organization != title
            )
        )
        for notice in notices:
            notice.organization = title


class OrganizationMove:
    """ Represents a single move of an adjacency list item. """

    def __init__(
        self,
        session: Session,
        subject_id: int,
        target_id: int,
        direction: MoveDirection
    ) -> None:

        self.session = session
        self.subject_id = subject_id
        self.target_id = target_id
        self.direction = direction

    def execute(self) -> None:
        from onegov.gazette.collections import OrganizationCollection

        organizations = OrganizationCollection(self.session)
        subject = organizations.by_id(self.subject_id)
        target = organizations.by_id(self.target_id)
        if subject and target and subject != target:
            if subject.parent_id == target.parent_id:
                OrganizationCollection(self.session).move(
                    subject=subject,
                    target=target,
                    direction=self.direction
                )
