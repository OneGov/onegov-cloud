from datetime import timedelta

from cached_property import cached_property
from sedate import utcnow

from onegov.core.elements import Link
from onegov.fsi.forms.course import months_to_timedelta
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


class AuditLayout(DefaultLayout):

    @cached_property
    def title(self):
        return _('Audit')

    @cached_property
    def breadcrumbs(self):
        links = super().breadcrumbs
        links.append(
            Link(_('Audit'), self.request.link(self.model))
        )
        return links

    @cached_property
    def editbar_links(self):
        return [
            Link(
                text=_("Print"),
                url='#',
                attrs={
                    'class': 'print-icon',
                    'onclick': 'window.print();return false;'
                }
            )
        ]

    def render_start_end(self, start, end):
        if not start:
            return '-'
        date_ = self.format_date(start, 'date')
        start = self.format_date(start, 'time')
        end = self.format_date(end, 'time')
        return f'{date_} {start} - {end}'

    def next_event_date(self, start, refresh_interval):
        if not start:
            return
        assert isinstance(refresh_interval, timedelta)
        return start + refresh_interval



