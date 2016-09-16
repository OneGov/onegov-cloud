from onegov.activity import ActivityCollection


class VacationActivityCollection(ActivityCollection):

    def __init__(self, session):
        super().__init__(session, type='vacation')
