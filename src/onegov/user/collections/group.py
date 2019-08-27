from onegov.user.models import UserGroup
from onegov.core.collection import GenericCollection


class UserGroupCollection(GenericCollection):
    """ Manages a list of user groups.

    Use it like this::

        from onegov.user import UserGroupCollection
        groups = UserGroupCollection(session)

    """

    def __init__(self, session, type='*'):
        self.session = session
        self.type = type

    @property
    def model_class(self):
        return UserGroup.get_polymorphic_class(self.type, default=UserGroup)

    def query(self):
        query = super(UserGroupCollection, self).query()
        return query.order_by(self.model_class.name)
