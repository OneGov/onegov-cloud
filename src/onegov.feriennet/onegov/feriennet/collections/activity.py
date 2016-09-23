from onegov.activity import ActivityCollection
from onegov.feriennet.security import ActivityQueryPolicy


class VacationActivityCollection(ActivityCollection):

    def __init__(self, session, identity=None, page=0, tags=None):
        super().__init__(session, type='vacation', page=page, tags=tags)
        self.identity = identity

    def subset(self):
        """ Limits the pagination results to activites visible by the
        current user.

        """
        policy = ActivityQueryPolicy.for_identity(self.identity)
        return policy.granted_subset(self.query())

    def page_by_index(self, index):
        return self.__class__(self.session, self.identity, page=index)
