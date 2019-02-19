from cached_property import cached_property
from onegov.core.elements import Link
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout


class ReportLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Report")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def dates(self):
        return "{}-{}".format(
            self.format_date(self.model.start, 'date'),
            self.format_date(self.model.end, 'date')
        )


class SpecificReportBaseLayout(DefaultLayout):

    @cached_property
    def subtitle(self):
        return "{}-{}".format(
            self.format_date(self.model.start, 'date'),
            self.format_date(self.model.end, 'date')
        )

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Report"), self.report_url),
            Link(self.title, "#"),
            Link(self.subtitle, self.request.link(self.model)),
        ]


class ReportBoxesLayout(SpecificReportBaseLayout):

    @cached_property
    def title(self):
        return _("Report boxes")


class ReportBoxesAndFormsLayout(SpecificReportBaseLayout):

    @cached_property
    def title(self):
        return _("Report boxes and forms")


class ReportFormsByMunicipalityLayout(SpecificReportBaseLayout):

    @cached_property
    def title(self):
        return _("Report forms")

    @cached_property
    def subtitle(self):
        return "{} {}-{}".format(
            self.model.municipality,
            self.format_date(self.model.start, 'date'),
            self.format_date(self.model.end, 'date')
        )
