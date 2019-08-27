from cached_property import cached_property
from onegov.wtfs.models.report import Report


class DailyList(object):
    pass


class DailyListBoxes(Report):
    """ All boxes of all municipalities on one day. """

    def __init__(self, session, date_=None):
        super().__init__(session, date_, date_)
        self.date = self.start
        self.type = 'normal'

    @cached_property
    def columns_dispatch(self):
        return [
            'dispatch_boxes',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
        ]

    @cached_property
    def columns_return(self):
        return ['return_boxes']


class DailyListBoxesAndForms(Report):
    """ All boxes of all municipalities on one day. """

    def __init__(self, session, date_=None):
        super().__init__(session, date_, date_)
        self.date = self.start
        self.type = 'normal'

    @cached_property
    def columns_dispatch(self):
        return [
            'dispatch_boxes',
            'dispatch_tax_forms_older',
            'dispatch_tax_forms_last_year',
            'dispatch_tax_forms_current_year',
            'dispatch_single_documents',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
        ]
