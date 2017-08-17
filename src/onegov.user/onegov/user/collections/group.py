from onegov.user.models import UserGroup
from onegov.core.collection import GenericCollection


class UserGroupCollection(GenericCollection):
    """ Manages a list of user groups.

    Use it like this::

        from onegov.user import UserGroupCollection
        groups = UserGroupCollection(session)

    """

    @property
    def model_class(self):
        return UserGroup

    def query(self):
        query = super(UserGroupCollection, self).query()
        return query.order_by(UserGroup.name)
