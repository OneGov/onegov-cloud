from __future__ import annotations

from onegov.core.html import html_to_text
from onegov.core.orm import Base
from onegov.core.orm.types import MarkupText, UUID
from onegov.fsi.i18n import _
from onegov.search import ORMSearchable
from sedate import utcnow
from sqlalchemy import Column, Text, Boolean, Integer
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import uuid
    from markupsafe import Markup
    from onegov.core.types import AppenderQuery
    from sqlalchemy.orm import Query
    from .course_event import CourseEvent


class Course(Base, ORMSearchable):
    __tablename__ = 'fsi_courses'

    fts_type_title = _('Courses')
    fts_public = True
    fts_title_property = 'name'
    fts_properties = {
        'name': {'type': 'localized', 'weight': 'A'},
        'description': {'type': 'localized', 'weight': 'B'},
    }

    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    name: Column[str] = Column(Text, nullable=False, unique=True)

    description: Column[Markup] = Column(MarkupText, nullable=False)

    # saved as integer (years), accessed as years
    refresh_interval: Column[int | None] = Column(Integer)

    # If the course has to be refreshed after some interval
    mandatory_refresh: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False
    )

    # hides the course in the collection for non-admins
    hidden_from_public: Column[bool] = Column(
        Boolean,
        nullable=False,
        default=False
    )

    evaluation_url: Column[str | None] = Column(Text)

    events: relationship[AppenderQuery[CourseEvent]] = relationship(
        'CourseEvent',
        back_populates='course',
        lazy='dynamic'
    )

    @property
    def title(self) -> str:
        return self.name

    @property
    def lead(self) -> str:
        text = html_to_text(self.description)

        if len(text) > 160:
            return text[:160] + '…'
        else:
            return text

    @property
    def description_html(self) -> Markup:
        """
        Returns the description that is saved as HTML from the redactor js
        plugin.
        """
        return self.description

    @hybrid_property
    def future_events(self) -> Query[CourseEvent]:
        from onegov.fsi.models import CourseEvent
        return self.events.filter(CourseEvent.start > utcnow()).order_by(
            CourseEvent.start)
