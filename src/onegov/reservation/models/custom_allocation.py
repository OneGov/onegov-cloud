from libres.db.models import Allocation
from onegov.core.orm import ModelBase
from onegov.reservation.models.resource import Resource
from sqlalchemy.orm import object_session


class CustomAllocation(Allocation, ModelBase):
    __mapper_args__ = {'polymorphic_identity': 'custom'}

    @property
    def resource_obj(self):
        return object_session(self).query(Resource)\
            .filter_by(id=self.resource).one()
