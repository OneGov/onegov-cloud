from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from sqlalchemy import Column
from sqlalchemy import Enum
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy.orm import object_session
from uuid import uuid4

from onegov.parliament import _

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Literal
    from typing import TypeAlias
    import uuid

    from onegov.core.orm.mixins import dict_property
    from onegov.parliament.models import Attendence
    from onegov.parliament.models import Commission
    from onegov.parliament.models import Parliamentarian

    Action: TypeAlias = Literal[
        'add',
        'edit',
        'delete'
    ]

ACTIONS: list[Action] = [
    'add',
    'edit',
    'delete',
]


class Change(Base, ContentMixin, TimestampMixin):

    __tablename__ = 'par_changes'

    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'generic',
    }

    #: Internal ID
    id: Column[uuid.UUID] = Column(
        UUID,  # type:ignore[arg-type]
        primary_key=True,
        default=uuid4
    )

    #: The user id responsible for the change
    user_id: Column[str | None] = Column(
        String,
        nullable=True
    )

    #: The username responsible for the change
    user_name: Column[str | None] = Column(
        String,
        nullable=True
    )

    @property
    def user(self) -> str | None:
        if (
            self.user_name
            and self.user_id
            and self.user_name != self.user_id
        ):
            return f'{self.user_name} ({self.user_id})'
        return self.user_name or self.user_id

    #: The type of change
    action: Column[Action] = Column(
        Enum(
            *ACTIONS,  # type:ignore[arg-type]
            name='par_actions'
        ),
        nullable=False
    )

    @property
    def action_label(self) -> str:
        if self.action == 'add' and self.model == 'attendence':
            return _('Attendence added')
        if self.action == 'edit' and self.model == 'attendence':
            return _('Attendence modified')
        if self.action == 'delete' and self.model == 'attendence':
            return _('Attendence removed')
        raise NotImplementedError()

    #: The model behind this change
    model: Column[str] = Column(
        String,
        nullable=False
    )

    @property
    def attendence(self) -> Attendence | None:
        from onegov.parliament.models import Attendence
        attendence_id = (self.changes or {}).get('id')
        if self.model == 'attendence' and attendence_id:
            session = object_session(self)
            query = session.query(Attendence).filter_by(id=attendence_id)
            return query.first()
        return None

    #: The changes
    changes: dict_property[dict[str, str | int | None] | None]
    changes = content_property()

    @property
    def date(self) -> date | None:
        date_string = (self.changes or {}).get('date')
        if date_string:
            assert isinstance(date_string, str)
            return date.fromisoformat(date_string)
        return None

    @property
    def parliamentarian(self) -> Parliamentarian | None:
        from onegov.parliament.models import Parliamentarian
        parliamentarian_id = (self.changes or {}).get('parliamentarian_id')
        if self.model == 'attendence' and parliamentarian_id:
            session = object_session(self)
            query = session.query(Parliamentarian).filter_by(
                id=parliamentarian_id
            )
            return query.first()
        return None

    @property
    def commission(self) -> Commission | None:
        from onegov.parliament.models import Commission
        commission_id = (self.changes or {}).get('commission_id')
        if self.model == 'attendence' and commission_id:
            session = object_session(self)
            query = session.query(Commission).filter_by(id=commission_id)
            return query.first()
        return None
