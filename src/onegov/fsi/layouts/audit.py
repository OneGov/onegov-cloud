from __future__ import annotations

from datetime import timedelta

from functools import cached_property

from onegov.core.elements import Link, LinkGroup
from onegov.fsi.layout import DefaultLayout
from onegov.fsi import _


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.fsi.collections.audit import AuditCollection


class AuditLayout(DefaultLayout):

    model: AuditCollection

    @property
    def title(self) -> str:
        return _('Audit')

    @cached_property
    def breadcrumbs(self) -> list[Link]:
        links = super().breadcrumbs
        assert isinstance(links, list)
        links.append(
            Link(_('Audit'), self.request.link(self.model))
        )
        return links

    @cached_property
    def editbar_links(self) -> list[Link | LinkGroup]:
        if not self.model.course_id or not self.model.subset_count:
            return []
        return [
            Link(
                text=_('PDF'),
                url=self.request.link(self.model, name='pdf'),
                attrs={'class': 'print-icon', 'target': '_blank'}
            ),
        ]

    def render_start_end(
        self,
        start: datetime | None,
        end: datetime | None
    ) -> str:
        if not start:
            return '-'
        date_str = self.format_date(start, 'date')
        start_str = self.format_date(start, 'time')
        end_str = self.format_date(end, 'time')
        return f'{date_str} {start_str} - {end_str}'

    def format_refresh_interval(self, num_years: int) -> str:
        assert isinstance(num_years, int)
        return self.format_timedelta(
            # NOTE: Even though 365.25 would be more accurate, babel itself
            #       uses 365 to count the number of years, so this is the
            #       most reliable way to not encounter any drift (not that
            #       we'd expect to see num_years high enough for this to
            #       matter)
            timedelta(days=num_years * 365)
        )

    @staticmethod
    def next_event_date(
        start: datetime | None,
        refresh_interval: int | None
    ) -> datetime | None:
        if not start:
            return None
        if refresh_interval is None:
            return None
        assert isinstance(refresh_interval, int)
        return start.replace(year=start.year + refresh_interval)

    @cached_property
    def audit_table_headers(self) -> list[str]:
        if not self.model.course:
            # FIXME: Maybe it would be better to assert this? It doesn't
            #        look like we expect to be able to deal with this case
            #        anywhere
            return []

        # FIXME: Does this mean this should actually not be nullable?
        assert self.model.course.refresh_interval is not None
        due_in = self.format_refresh_interval(
            self.model.course.refresh_interval)
        titles = (
            _('Name'),
            _('Shortcode'),
            _('Last Event'),
            _('Registered'),
            _('Due by (every ${refresh_interval})', mapping={
                'refresh_interval': due_in}
              )
        )
        return [self.request.translate(head) for head in titles]
