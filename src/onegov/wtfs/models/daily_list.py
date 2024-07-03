from functools import cached_property
from onegov.wtfs.models.report import Report


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from sqlalchemy.orm import Session


class DailyList:
    pass


class DailyListBoxes(Report):
    """ All boxes of all municipalities on one day. """

    def __init__(
        self,
        session: 'Session',
        date_: 'date | None' = None
    ):
        super().__init__(session, date_, date_)
        self.date = self.start
        self.type = 'normal'

    @cached_property
    def columns_dispatch(self) -> list[str]:
        return [
            'dispatch_boxes',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
        ]

    @cached_property
    def columns_return(self) -> list[str]:
        return ['return_boxes']


class DailyListBoxesAndForms(Report):
    """ All boxes of all municipalities on one day. """

    def __init__(
        self,
        session: 'Session',
        date_: 'date | None' = None
    ):
        super().__init__(session, date_, date_)
        self.date = self.start
        self.type = 'normal'

    @cached_property
    def columns_dispatch(self) -> list[str]:
        return [
            'dispatch_boxes',
            'dispatch_tax_forms_older',
            'dispatch_tax_forms_last_year',
            'dispatch_tax_forms_current_year',
            'dispatch_single_documents',
            'dispatch_cantonal_tax_office',
            'dispatch_cantonal_scan_center',
        ]
