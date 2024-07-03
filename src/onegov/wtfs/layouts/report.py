from functools import cached_property
from onegov.core.elements import Link
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.core.elements import Element


class ReportLayout(DefaultLayout):

    @cached_property
    def title(self) -> str:
        return _("Report")

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.request.link(self.model))
        ]

    @cached_property
    def dates(self) -> str:
        return "{}-{}".format(
            self.format_date(self.model.start, 'date'),
            self.format_date(self.model.end, 'date')
        )


class SpecificReportBaseLayout(DefaultLayout):

    @cached_property
    def subtitle(self) -> str:
        return "{}-{}".format(
            self.format_date(self.model.start, 'date'),
            self.format_date(self.model.end, 'date')
        )

    @cached_property
    def editbar_links(self) -> list['Element']:
        return [
            Link(
                text=_("Print"),
                url='#',
                attrs={
                    'class': 'print-icon',
                }
            )
        ]

    @cached_property
    def breadcrumbs(self) -> list['Element']:
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Report"), self.report_url),
            Link(self.title, "#"),
            Link(self.subtitle, self.request.link(self.model)),
        ]


class ReportBoxesLayout(SpecificReportBaseLayout):

    @cached_property
    def title(self) -> str:
        return _("Report boxes")


class ReportBoxesAndFormsLayout(SpecificReportBaseLayout):

    @cached_property
    def title(self) -> str:
        return _("Report boxes and forms")


class ReportFormsByMunicipalityLayout(SpecificReportBaseLayout):

    @cached_property
    def title(self) -> str:
        return _("Report forms")

    @cached_property
    def subtitle(self) -> str:
        return "{} {}-{}".format(
            self.model.municipality_name,
            self.format_date(self.model.start, 'date'),
            self.format_date(self.model.end, 'date')
        )


class ReportFormsAllMunicipalitiesLayout(SpecificReportBaseLayout):

    @cached_property
    def title(self) -> str:
        return _("Report forms of all municipalities")


class ReportBoxesAndFormsByDeliveryLayout(SpecificReportBaseLayout):

    @cached_property
    def title(self) -> str:
        return _("Report boxes and forms by delivery")

    @cached_property
    def subtitle(self) -> str:
        return "{} ({}) {}-{}".format(
            self.model.municipality.name,
            self.model.municipality.bfs_number,
            self.format_date(self.model.start, 'date'),
            self.format_date(self.model.end, 'date')
        )
