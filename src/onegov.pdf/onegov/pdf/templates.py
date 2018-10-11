from pdfdocument.document import ReportingDocTemplate


class Template(ReportingDocTemplate):
    """ Extends the ReportingDocTemplate with Table of Contents printing. """

    def afterFlowable(self, flowable):

        ReportingDocTemplate.afterFlowable(self, flowable)

        if hasattr(flowable, 'toc_level'):
            self.notify('TOCEntry', (
                flowable.toc_level, flowable.getPlainText(), self.page,
                flowable.bookmark
            ))
