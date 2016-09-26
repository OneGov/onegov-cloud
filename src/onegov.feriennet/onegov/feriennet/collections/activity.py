from onegov.activity import ActivityCollection
from onegov.feriennet.security import ActivityQueryPolicy


class VacationActivityCollection(ActivityCollection):

    def __init__(self, session, identity, page=0, tags=None, states=None):
        super().__init__(
            session=session,
            type='vacation',
            page=page,
            tags=tags,
            states=states
        )
        self.identity = identity

    @property
    def policy(self):
        return ActivityQueryPolicy.for_identity(self.identity)

    def query_base(self):
        return self.policy.granted_subset(self.session.query(self.model_class))

    def page_by_index(self, index):
        return self.__class__(
            session=self.session,
            identity=self.identity,
            page=index,
            tags=self.tags,
            states=self.states
        )
