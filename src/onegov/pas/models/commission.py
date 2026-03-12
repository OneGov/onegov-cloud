from __future__ import annotations

from onegov.parliament.models import Commission
from onegov.pas.i18n import _
from onegov.search import ORMSearchable
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.pas.models import Attendence


class PASCommission(Commission, ORMSearchable):

    __mapper_args__ = {
        'polymorphic_identity': 'pas_commission',
    }

    fts_type_title = _('Commission')
    fts_public = False
    fts_title_property = 'name'
    fts_properties = {'name': {'type': 'text', 'weight': 'A'}}

    @property
    def fts_suggestion(self) -> str:
        return self.name

    #: A commission may hold meetings
    attendences: Mapped[list[Attendence]] = relationship(
        cascade='all, delete-orphan',
        back_populates='commission'
    )
