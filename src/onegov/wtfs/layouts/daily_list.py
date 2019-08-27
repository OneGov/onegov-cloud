from cached_property import cached_property
from onegov.core.elements import Link
from onegov.wtfs import _
from onegov.wtfs.layouts.default import DefaultLayout


class DailyListLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _("Daily list")

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(self.title, self.request.link(self.model)),
        ]


class SpecificDailyListBaseLayout(DefaultLayout):

    date_custom_format = 'EEEE dd. MMMM yyyy'

    @cached_property
    def subtitle(self):
        return self.format_date(self.model.date, 'date_custom')

    @cached_property
    def editbar_links(self):
        result = []
        result.append(
            Link(
                text=_("Print"),
                url='#',
                attrs={
                    'class': 'print-icon',
                    'onclick': 'window.print();return false;'
                }
            )
        )
        return result

    @cached_property
    def breadcrumbs(self):
        return [
            Link(_("Homepage"), self.homepage_url),
            Link(_("Daily list"), self.daily_list_url),
            Link(self.title, "#"),
            Link(self.subtitle, self.request.link(self.model)),
        ]


class DailyListBoxesLayout(SpecificDailyListBaseLayout):

    @cached_property
    def title(self):
        return _("Boxes")


class DailyListBoxesAndFormsLayout(SpecificDailyListBaseLayout):

    @cached_property
    def title(self):
        return _("Boxes and forms")
