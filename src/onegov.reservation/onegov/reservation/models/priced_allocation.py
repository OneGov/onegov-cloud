from libres.db.models import Allocation
from onegov.core.orm import ModelBase


class PricedAllocation(Allocation, ModelBase):
    __mapper_args__ = {'polymorphic_identity': 'priced'}
