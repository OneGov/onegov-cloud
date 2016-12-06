class BillingCollection(object):

    def __init__(self, session, period):
        self.session = session
        self.period = period

    @property
    def period_id(self):
        return self.period.id

    def for_period(self, period):
        return self.__class__(self.session, period)

    @property
    def bills(self):
        return []
