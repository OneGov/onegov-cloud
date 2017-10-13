from onegov.activity import ActivityCollection
from onegov.feriennet.policy import ActivityQueryPolicy
from sqlalchemy.orm import joinedload


class VacationActivityCollection(ActivityCollection):

    def __init__(self, session, identity, page=0,
                 tags=None,
                 states=None,
                 durations=None,
                 age_ranges=None,
                 owners=None,
                 period_ids=None,
                 dateranges=None,
                 weekdays=None,
                 municipalities=None,
                 available=None):
        super().__init__(
            session=session,
            type='vacation',
            page=page,
            tags=tags,
            states=states,
            durations=durations,
            age_ranges=age_ranges,
            owners=owners,
            period_ids=period_ids,
            dateranges=dateranges,
            weekdays=weekdays,
            municipalities=municipalities,
            available=available
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
            tags=self.tags,
            states=self.states,
            durations=self.durations,
            age_ranges=self.age_ranges,
            owners=self.owners,
            period_ids=self.period_ids,
            dateranges=self.dateranges,
            weekdays=self.weekdays,
            municipalities=self.municipalities,
            available=self.available
        )
