from __future__ import annotations

from onegov.parliament.models import Parliamentarian
from onegov.pas.i18n import _
from onegov.pas.models.parliamentarian_role import PASParliamentarianRole
from onegov.search import ORMSearchable
from sqlalchemy import or_
from sqlalchemy.orm import backref, relationship, Mapped


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.pas.models import Attendence
    from onegov.pas.models import Party
    from onegov.user import User
    from sqlalchemy.orm import Session


class PASParliamentarian(Parliamentarian, ORMSearchable):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_parliamentarian',
    }

    fts_type_title = _('Parliamentarians')
    fts_public = False
    fts_title_property = 'title'
    fts_properties = {
        # FIXME: A fullname property may yield better results
        'first_name': {'type': 'text', 'weight': 'A'},
        'last_name': {'type': 'text', 'weight': 'A'},
    }

    @property
    def fts_suggestion(self) -> tuple[str, ...]:
        return (
            f'{self.first_name} {self.last_name}',
            f'{self.last_name} {self.first_name}'
        )

    #: A parliamentarian may attend meetings
    attendences: Mapped[list[Attendence]] = relationship(
        cascade='all, delete-orphan',
        back_populates='parliamentarian'
    )

    # the user account related to this parliamentarian
    user: Mapped[User] = relationship(
        primaryjoin='foreign(PASParliamentarian.email_primary) == '
                    'User.username',
        backref=backref('parliamentarian', uselist=False,
                        passive_deletes='all')
    )

    if TYPE_CHECKING:
        roles: Mapped[list[PASParliamentarianRole]]  # type: ignore[assignment]

    def get_party_during_period(
        self, start_date: date, end_date: date, session: Session
    ) -> Party | None:
        """Get the party this parliamentarian belonged to during a specific
        period.

        Note: If you find yourself calling this in a loop, it's not
            recommended. Pre-fetch `PASParliamentarianRole` first.
        """

        role = (
            session.query(PASParliamentarianRole)
            .filter(
                PASParliamentarianRole.parliamentarian_id == self.id,
                PASParliamentarianRole.party_id.isnot(
                    None
                ),
                or_(
                    PASParliamentarianRole.end.is_(None),
                    PASParliamentarianRole.end >= start_date,
                ),
                PASParliamentarianRole.start
                <= end_date,
            )
            .order_by(PASParliamentarianRole.start.desc())
            .first()
        )

        return role.party if role else None
