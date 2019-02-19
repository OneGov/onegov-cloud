from onegov.wtfs.models.report import Report


class DailyList(Report):

    def __init__(self, session, date_=None):
        super().__init__(session, date_, date_)
        self.date = self.start
