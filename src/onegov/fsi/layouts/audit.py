from datetime import timedelta

from cached_property import cached_property

from onegov.core.elements import Link
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
        if not self.model.course_id or not self.model.subset_count:
            return []
        return [
            Link(
                text=_("PDF"),
                url=self.request.link(self.model, name='pdf'),
                attrs={'class': 'print-icon', 'target': '_blank'}
            ),
        ]

    def render_start_end(self, start, end):
        if not start:
            return '-'
        date_ = self.format_date(start, 'date')
        start = self.format_date(start, 'time')
        end = self.format_date(end, 'time')
        return f'{date_} {start} - {end}'

    def format_refresh_interval(self, num_years):
        assert isinstance(num_years, int)
        return self.format_timedelta(
            timedelta(days=num_years * 365)
        )

    @staticmethod
    def next_event_date(start, refresh_interval):
        if not start:
            return
        if refresh_interval is None:
            return
        assert isinstance(refresh_interval, int)
        return start.replace(year=start.year + refresh_interval)

    @cached_property
    def audit_table_headers(self):
        if not self.model.course:
            return ""
        due_in = self.format_refresh_interval(
            self.model.course.refresh_interval)
        titles = (
            _("Name"),
            _("Shortcode"),
            _("Last Event"),
            _("Attended"),
            _("Due by (every ${refresh_interval})", mapping={
                'refresh_interval': due_in}
              )
        )
        return [self.request.translate(head) for head in titles]
