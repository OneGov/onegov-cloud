from libres.db.models import Allocation
from onegov.core.orm import ModelBase
from onegov.reservation.models.resource import Resource
from sqlalchemy.orm import object_session


class CustomAllocation(Allocation, ModelBase):
    __mapper_args__ = {'polymorphic_identity': 'custom'}  # type:ignore

    @property
    def resource_obj(self) -> Resource:
        return object_session(self).query(
            Resource).filter_by(id=self.resource).one()

    @property
    def access(self) -> str:
        # FIXME: While we might prefer this to be an extension
        #        that's performed by other modules, that would
        #        force us to change the polymorphic type of
        #        existing allocations in order for this setting
        #        to work. So we just do it here for now...
        return (self.data or {}).get('access', 'public')
