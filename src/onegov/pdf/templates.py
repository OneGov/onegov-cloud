from __future__ import annotations

from pdfdocument.document import ReportingDocTemplate


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from reportlab.platypus.flowables import Flowable


class Template(ReportingDocTemplate):
    """ Extends the ReportingDocTemplate with Table of Contents printing. """

    def afterFlowable(self, flowable: Flowable) -> None:

        ReportingDocTemplate.afterFlowable(self, flowable)

        # FIXME: This isn't very clean we should just create a subclass
        #        of Paragraph called TOCHeading or something like that
        #        which we use for these markers
        if hasattr(flowable, 'toc_level'):
            assert hasattr(flowable, 'getPlainText')
            assert hasattr(flowable, 'bookmark')
            self.notify('TOCEntry', (
                flowable.toc_level, flowable.getPlainText(), self.page,
                flowable.bookmark
            ))
