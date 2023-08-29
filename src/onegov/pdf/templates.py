from pdfdocument.document import ReportingDocTemplate


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from reportlab.platypus.flowables import Flowable


class Template(ReportingDocTemplate):
    """ Extends the ReportingDocTemplate with Table of Contents printing. """

    def afterFlowable(self, flowable: 'Flowable') -> None:

        ReportingDocTemplate.afterFlowable(self, flowable)

        if hasattr(flowable, 'toc_level'):
            self.notify('TOCEntry', (
                flowable.toc_level, flowable.getPlainText(), self.page,
                flowable.bookmark
            ))
