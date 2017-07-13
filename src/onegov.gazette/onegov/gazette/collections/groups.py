from onegov.gazette.models import UserGroup
from onegov.core.collection import GenericCollection


class UserGroupCollection(GenericCollection):

    @property
    def model_class(self):
        return UserGroup

    def query(self):
        query = super(UserGroupCollection, self).query()
        return query.order_by(UserGroup.name)
