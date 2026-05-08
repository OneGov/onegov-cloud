from __future__ import annotations

from libres.db.models import Allocation
from onegov.core.orm import ModelBase
from onegov.reservation.models.resource import Resource
from sqlalchemy.orm import object_session


class CustomAllocation(Allocation, ModelBase):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

    @property
    def resource_obj(self) -> Resource:
        session = object_session(self)
        assert session is not None
        return session.query(
            Resource).filter_by(id=self.resource).one()

    @property
    def access(self) -> str:
        return (self.data or {}).get('access', 'public')
