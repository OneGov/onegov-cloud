from onegov.core.orm import Base
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import MarkupText
from onegov.core.orm.types import UTCDateTime
from onegov.core.orm.types import UUID
from onegov.user import User
from onegov.user import UserGroup
from sedate import utcnow
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Text
from sqlalchemy.dialects.postgresql import HSTORE
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.orm import backref
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import Literal, TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from collections.abc import Iterable
    from datetime import datetime
    from markupsafe import Markup

NoticeState = Literal[
    'drafted',
    'submitted',
    'rejected',
    'imported',
    'accepted',
    'published',
]


class OfficialNotice(Base, ContentMixin, TimestampMixin):

    """ Defines an official notice.

    The notice follows a typcical state transition: drafted by an editor ->
    submitted by and editor to a publisher -> accepted by a publisher ->
    published by the publisher. It may be alternatively rejected by a publisher
    when submitted.

    The notice typically has a title and a text, belongs to a user and a user
    group, appears in one ore more issues and belongs to one or more categories
    and organizations.

    You can set the date of the first issue besides setting the issues (to
    allow filtering by date for example).

    You can set the category and organization directly instead of using the
    HSTOREs (or use both).

    """

    __tablename__ = 'official_notices'

    #: the type of the item, this can be used to create custom polymorphic
    #: subclasses of this class. See
    #: `<https://docs.sqlalchemy.org/en/improve_toc/\
    #: orm/extensions/declarative/inheritance.html>`_.
    type: 'Column[str]' = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic'
    }

    #: The internal ID of the notice.
    id: 'Column[uuid.UUID]' = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: A nice ID usable for the url, readable by humans.
    # FIXME: Should this be nullable=True?
    name: 'Column[str | None]' = Column(Text)

    #: The state of the notice.
    state: 'Column[NoticeState]' = Column(
        Enum(  # type:ignore[arg-type]
            'drafted',
            'submitted',
            'rejected',
            'imported',
            'accepted',
            'published',
            name='official_notice_state'
        ),
        nullable=False,
        default='drafted'
    )

    #: The title of the notice.
    title: 'Column[str]' = Column(Text, nullable=False)

    #: The text of the notice.
    text: 'Column[Markup | None]' = Column(MarkupText, nullable=True)

    #: The author of the notice.
    author_name: 'Column[str | None]' = Column(Text, nullable=True)

    #: The place (part of the signature).
    author_place: 'Column[str | None]' = Column(Text, nullable=True)

    #: The date (part of the signature)
    author_date: 'Column[datetime | None]' = Column(UTCDateTime, nullable=True)

    #: A note to the notice.
    note: 'Column[str | None]' = Column(Text, nullable=True)

    #: The issues this notice appears in.
    _issues: 'Column[dict[str, str | None]]' = Column(  # type:ignore
        MutableDict.as_mutable(HSTORE), name='issues', nullable=True
    )

    @property
    def issues(self) -> dict[str, str | None]:
        return self._issues or {}

    # FIXME: mypy doesn't allow asymmetric properties, so assigning everything
    #        other than a dict will resolve in a type error. We could make a
    #        custom descriptor, but it doesn't seem worth it, it seems better
    #        to just always pass in a dict. Once everything is fully type
    #        checked we can simplify the implementation.
    @issues.setter
    def issues(self, value: 'dict[str, str | None] | Iterable[str]') -> None:
        if isinstance(value, dict):
            self._issues = value
        else:
            self._issues = {item: None for item in value}

    #: The date of the first issue of the notice.
    first_issue: 'Column[datetime | None]' = Column(UTCDateTime, nullable=True)

    #: The expiry date of the notice
    expiry_date: 'Column[datetime | None]' = Column(UTCDateTime, nullable=True)

    @property
    def expired(self) -> bool:
        """ Returns True, if the notice is expired. """

        if self.expiry_date:
            return self.expiry_date < utcnow()
        return False

    #: The categories of this notice.
    _categories: 'Column[dict[str, str | None]]' = Column(  # type:ignore
        MutableDict.as_mutable(HSTORE), name='categories', nullable=True
    )

    @property
    def categories(self) -> dict[str, str | None]:
        return self._categories or {}

    # FIXME: Same issue as with issues.setter
    @categories.setter
    def categories(
        self,
        value: 'dict[str, str | None] | Iterable[str]'
    ) -> None:
        if isinstance(value, dict):
            self._categories = value
        else:
            self._categories = {item: None for item in value}

    #: The category of the notice.
    category: 'Column[str | None]' = Column(Text, nullable=True)

    #: The organization this notice belongs to.
    organization: 'Column[str | None]' = Column(Text, nullable=True)

    #: The organizations of this notice.
    _organizations: 'Column[dict[str, str | None] | None]'
    _organizations = Column(  # type:ignore[call-overload]
        MutableDict.as_mutable(HSTORE), name='organizations', nullable=True
    )

    @property
    def organizations(self) -> dict[str, str | None]:
        return self._organizations or {}

    # FIXME: Same issue as with issues.setter
    @organizations.setter
    def organizations(
        self,
        value: 'dict[str, str | None] | Iterable[str]'
    ) -> None:
        if isinstance(value, dict):
            self._organizations = value
        else:
            self._organizations = {item: None for item in value}

    #: The user that owns this notice.
    user_id: 'Column[uuid.UUID | None]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(User.id),
        nullable=True
    )
    user: 'relationship[User | None]' = relationship(
        User, backref=backref('official_notices', lazy='select')
    )

    #: The group that owns this notice.
    group_id: 'Column[uuid.UUID | None]' = Column(
        UUID,  # type:ignore[arg-type]
        ForeignKey(UserGroup.id),
        nullable=True
    )
    group: 'relationship[UserGroup | None]' = relationship(
        UserGroup, backref=backref('official_notices', lazy='select')
    )

    #: The source from where this notice has been imported.
    source: 'Column[str | None]' = Column(Text, nullable=True)

    def submit(self) -> None:
        """ Submit a drafted notice. """

        assert self.state == 'drafted' or self.state == 'rejected'
        self.state = 'submitted'

    def reject(self) -> None:
        """ Reject a submitted notice. """

        assert self.state == 'submitted'
        self.state = 'rejected'

    def accept(self) -> None:
        """ Accept a submitted notice. """

        assert self.state == 'submitted' or self.state == 'imported'
        self.state = 'accepted'

    def publish(self) -> None:
        """ Publish an accepted notice. """

        assert self.state == 'accepted'
        self.state = 'published'
