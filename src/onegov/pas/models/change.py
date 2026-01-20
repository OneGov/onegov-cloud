from __future__ import annotations

from datetime import date
from onegov.core.orm import Base
from onegov.core.orm.mixins import content_property
from onegov.core.orm.mixins import ContentMixin
from onegov.core.orm.mixins import TimestampMixin
from onegov.core.orm.types import UUID
from onegov.pas import _
from onegov.pas.models.attendence import Attendence
from onegov.pas.models.commission import PASCommission
from onegov.pas.models.parliamentarian import PASParliamentarian
from sqlalchemy import Column, Text
from sqlalchemy import Enum
from sqlalchemy import String
from sqlalchemy.orm import object_session
from uuid import uuid4


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from typing import Literal
    from typing import TypeAlias
    import uuid

    from onegov.core.orm.mixins import dict_property
    from onegov.town6.request import TownRequest

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

    #: The polymorphic type of change
    type: Column[str] = Column(
        Text,
        nullable=False,
        default=lambda: 'generic'
    )

    __mapper_args__ = {
        'polymorphic_on': type,
        'polymorphic_identity': 'pas_change',
    }

    @property
    def attendence(self) -> Attendence | None:
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
    def parliamentarian(self) -> PASParliamentarian | None:
        parliamentarian_id = (self.changes or {}).get('parliamentarian_id')
        if self.model == 'attendence' and parliamentarian_id:
            session = object_session(self)
            query = session.query(PASParliamentarian).filter_by(
                id=parliamentarian_id
            )
            return query.first()
        return None

    @property
    def commission(self) -> PASCommission | None:
        commission_id = (self.changes or {}).get('commission_id')
        if self.model == 'attendence' and commission_id:
            session = object_session(self)
            query = session.query(PASCommission).filter_by(id=commission_id)
            return query.first()
        return None

    @classmethod
    def add(
        cls,
        request: TownRequest,
        action: Action,
        attendence: Attendence
    ) -> Change:
        """ Create a new change and add it to the session. """

        change = cls()
        change.user_id = request.current_username
        change.user_name = (
            request.current_user.title if request.current_user else None
        )
        change.action = action
        change.model = 'attendence'
        change.changes = {
            'id': str(attendence.id),
            'date': attendence.date.isoformat(),
            'duration': attendence.duration,
            'type': attendence.type,
            'parliamentarian': (
                attendence.parliamentarian.title
                if attendence.parliamentarian else ''
            ),
            'parliamentarian_id': str(attendence.parliamentarian_id),
            'commission_id': str(attendence.commission_id or ''),
            'commission': (
                attendence.commission.title
                if attendence.commission else ''
            ),
        }
        request.session.add(change)
        return change
