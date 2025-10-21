from __future__ import annotations

from copy import deepcopy
from datetime import date
from io import BytesIO

from itertools import groupby
from markupsafe import Markup
from onegov.org import _
from onegov.org.layout import DefaultLayout
from onegov.org.pdf.core import OrgPdf
from onegov.reservation import Resource
from pdfdocument.document import MarkupParagraph
from reportlab.lib.enums import TA_RIGHT
from reportlab.platypus import PageBreak


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import datetime
    from onegov.org.request import OrgRequest
    from onegov.org.utils import MyReservationEventInfo


class MyReservationsPdf(OrgPdf):

    def add_reservations(
        self,
        infos: list[MyReservationEventInfo],
        start: datetime,
        end: datetime,
        request: OrgRequest
    ) -> None:
        """ Adds reservations to the story. """

        layout = DefaultLayout(None, request)

        self.h1(_('My Reservations'))
        self.h2(
            f"{layout.format_date(start, 'date_long')} - "
            f"{layout.format_date(end, 'date_long')}"
        )

        if not infos:
            self.spacer()
            self.p_markup(_('No data available'))
            return

        current_year: int | None = None
        current_month: str | None = None
        for dt, group in groupby(infos, key=lambda info: info.start.date()):
            if current_year:
                self.spacer()
            with self.keep_together():
                month = layout.format_date(dt, 'month_long')
                if current_year != dt.year or current_month != month:
                    current_year = dt.year
                    current_month = month
                    self.h2(f'{current_month} {current_year}')
                day_style = deepcopy(self.style.bold)
                day_style.alignment = TA_RIGHT
                event_data = sorted(
                    (info.event_time, info.event_title)
                    for info in group
                )
                self.table([
                    [
                        MarkupParagraph(
                            layout.format_date(dt, 'date'),
                            style=deepcopy(self.style.bold)
                        ),
                        MarkupParagraph(
                            layout.format_date(dt, 'weekday_long'),
                            style=deepcopy(self.style.bold)
                        )
                    ],
                    *(
                        [
                            MarkupParagraph(event_time),
                            MarkupParagraph(Markup('<br/>').join(
                                Markup('<b>{}</b>').format(line)
                                if idx == 0 else line
                                for idx, line in enumerate(
                                    event_title.splitlines()
                                )
                                if line != event_time
                            ))
                        ]
                        for event_time, event_title in event_data
                    )
                ], [.2, .8], ratios=True, first_bold=False)

    def resource_infos(self, resources: list[Resource]) -> None:
        first = True
        for resource in resources:
            confirmation_text = getattr(resource, 'confirmation_text', None)
            if not confirmation_text:
                continue

            self.story.append(PageBreak())
            if first:
                first = False
                self.h1('Appendix')
            else:
                self.spacer()
            self.h2(resource.title)
            self.mini_html(confirmation_text)

    @classmethod
    def from_reservations(
        cls,
        request: OrgRequest,
        infos: list[MyReservationEventInfo],
        start: datetime,
        end: datetime,
    ) -> BytesIO:
        """
        Creates a PDF representation of the reservations.
        """
        layout = DefaultLayout(None, request)
        result = BytesIO()
        pdf = cls(
            result,
            title=f"{request.translate(_('My Reservations'))} "
            f"{layout.format_date(start, 'date')} - "
            f"{layout.format_date(end, 'date')}",
            created=f'{date.today():%d.%m.%Y}',
            link_color='#00538c',
            underline_links=True,
            author=request.host_url,
            translations=request.app.translations,
            locale=request.locale,
        )
        pdf.init_a4_portrait(
            page_fn=pdf.page_fn,
            page_fn_later=pdf.page_fn_later
        )
        pdf.add_reservations(infos, start, end, request)

        resource_ids = {info.resource_id for info in infos}
        resources = (
            request.app.libres_resources.query()
            .filter(Resource.id.in_(resource_ids))
            .order_by(Resource.title.asc())
            .all()
        )
        pdf.resource_infos(resources)

        pdf.generate()
        result.seek(0)
        return result
