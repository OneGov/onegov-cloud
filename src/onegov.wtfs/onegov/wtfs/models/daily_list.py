from onegov.wtfs.models.report import Report


class DailyList(object):
    pass


class DailyListBoxes(Report):
    """ All boxes of all municipalities on one day. """

    def __init__(self, session, date_=None):
        super().__init__(session, date_, date_)
        self.date = self.start
