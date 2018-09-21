from onegov.activity import ActivityCollection
from onegov.feriennet.policy import ActivityQueryPolicy
from sqlalchemy.orm import joinedload


class VacationActivityCollection(ActivityCollection):

    # type is ignored, but present to keep the same signature as the superclass
    def __init__(self, session, type=None, page=0, filter=None, identity=None):
        super().__init__(
            session=session,
            type='vacation',
            page=page,
            filter=filter
        )

        self.identity = identity

    @property
    def policy(self):
        return ActivityQueryPolicy.for_identity(self.identity)

    def transform_batch_query(self, query):
        return query.options(joinedload('occasions'))

    def query_base(self):
        return self.policy.granted_subset(self.session.query(self.model_class))

    def page_by_index(self, index):
        return self.__class__(
            session=self.session,
            identity=self.identity,
            page=index,
            filter=self.filter
        )
