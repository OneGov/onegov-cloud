from __future__ import annotations

from markupsafe import Markup
from onegov.core.html import html_to_text
from onegov.core.orm import Base
from onegov.fsi.i18n import _
from onegov.search import ORMSearchable
from sedate import utcnow
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import DynamicMapped
from sqlalchemy.orm import Mapped
from uuid import uuid4, UUID


from typing import TYPE_CHECKING
if TYPE_CHECKING:
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

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4
    )

    name: Mapped[str] = mapped_column(unique=True)

    description: Mapped[Markup]

    # saved as integer (years), accessed as years
    refresh_interval: Mapped[int | None]

    # If the course has to be refreshed after some interval
    mandatory_refresh: Mapped[bool] = mapped_column(default=False)

    # hides the course in the collection for non-admins
    hidden_from_public: Mapped[bool] = mapped_column(default=False)

    evaluation_url: Mapped[str | None]

    events: DynamicMapped[CourseEvent] = relationship(back_populates='course')

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
