from __future__ import annotations

from datetime import date
from io import BytesIO
from operator import itemgetter
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from sedate import utcnow

from onegov.fsi import _
from onegov.pdf import Pdf, page_fn_footer, page_fn_header_and_footer


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from onegov.fsi.collections.audit import AuditCollection
    from onegov.fsi.collections.subscription import SubscriptionsCollection
    from onegov.fsi.models import CourseSubscription
    from onegov.fsi.layout import DefaultLayout
    from onegov.fsi.layouts.audit import AuditLayout
    from onegov.pdf.templates import Template
    from reportlab.lib.colors import Color
    from reportlab.pdfgen.canvas import Canvas


class FsiPdf(Pdf):

    previous_level_context: int | None = None

    @property
    def page_fn(self) -> Callable[[Canvas, Template], None]:
        return page_fn_footer

    @property
    def page_fn_later(self) -> Callable[[Canvas, Template], None]:
        return page_fn_header_and_footer

    @property
    def table_style(self) -> list[tuple[Any, ...]]:
        return [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]

    @classmethod
    def from_subscriptions(
        cls,
        collection: SubscriptionsCollection,
        layout: DefaultLayout,
        title: str
    ) -> BytesIO:

        chosen_event = layout.model.course_event
        translate = layout.request.translate
        result = BytesIO()
        pdf = cls(
            result,
            title=title,
            created=f'{date.today():%d.%m.%Y}',
        )
        pdf.init_a4_portrait(
            page_fn=pdf.page_fn,
            page_fn_later=pdf.page_fn_later
        )

        pdf.h(title)
        pdf.p(f"{translate(_('Printed'))} "
              f"{layout.format_date(utcnow(), 'date')}")

        pdf.spacer()

        def get_headers() -> list[str]:
            headers = ['Attendee', 'Shortcode']
            if not chosen_event:
                headers.append('Course Name')
                headers.append('Date')
            headers += ['Course Status', 'Course attended', 'Last info mail']
            return [translate(_(h)) for h in headers]

        def get_row(subscription: CourseSubscription) -> list[str]:
            row = [str(subscription)]
            att = subscription.attendee
            row.append(att and att.source_id or '')

            if not chosen_event:
                event = subscription.course_event
                row.append(event.name)
                row.append(
                    layout.format_date(event.start, 'datetime')
                )
                sent = event.info_template.last_sent
            else:
                sent = chosen_event.info_template.last_sent

            row.append(
                translate(layout.format_status(
                    chosen_event.status if chosen_event else event.status))
            )
            row.append('✔' if subscription.event_completed else '-')
            row.append(layout.format_date(sent, 'date') if sent else '')
            return row

        data = sorted(
            (get_row(subs) for subs in collection.query()),
            key=itemgetter(0)
        )
        data.insert(0, get_headers())

        pdf.table(
            data,
            columns='even',
            style=pdf.table_style,
        )
        pdf.generate()
        result.seek(0)
        return result

    @classmethod
    def from_audit_collection(
        cls,
        collection: AuditCollection,
        layout: AuditLayout,
        title: str
    ) -> BytesIO:

        now = utcnow()
        request = layout.request
        assert collection.course is not None
        refresh_interval = collection.course.refresh_interval
        result = BytesIO()
        pdf = cls(
            result,
            title=title,
            created=f'{date.today():%d.%m.%Y}',
        )
        pdf.init_a4_portrait(
            page_fn=pdf.page_fn,
            page_fn_later=pdf.page_fn_later
        )

        pdf.h(title)
        filter_str = ''
        if collection.organisations:
            orgs = ', '.join(collection.organisations)
            org_title = request.translate(_('Organisations'))
            filter_str = f'{org_title}: {orgs}'

        if collection.letter:
            letter_title = request.translate(_('Letter'))
            letter_title += f' {collection.letter}'

            if filter_str:
                filter_str += f'{filter_str}, {letter_title}'
            else:
                filter_str = letter_title

        if filter_str:
            pdf.h3(filter_str)

        pdf.p(f"{request.translate(_('Printed'))} "
              f"{layout.format_date(now, 'date')}")

        pdf.spacer()

        data: list[list[Any]] = [layout.audit_table_headers]

        green = HexColor('#1be45b')
        orange = HexColor('#f4cb71')
        red = colors.pink

        style = pdf.table_style

        def bgcolor(ix: int, row: int, color: Color) -> tuple[Any, ...]:
            return 'BACKGROUND', (row, ix), (row, ix), color

        next_subscriptions = collection.next_subscriptions(request)

        for ix, e in enumerate(collection.query()):
            dt = layout.next_event_date(e.start, refresh_interval)
            if dt:
                if now > dt:
                    next_event_hint = dt.year
                    color = red
                else:
                    not_so_fine = (dt.year == now.year and e.event_completed)
                    color = orange if not_so_fine else green
                    next_event_hint = dt.year
            else:
                next_event_hint = now.year
                color = red
            style.append(bgcolor(ix + 1, 4, color))

            data_line = [
                f'{e.last_name}, {e.first_name}',
                e.source_id,
                layout.format_date(e.start, 'datetime'),
                '✔' if next_subscriptions.get(e[0], None) else '-',
                next_event_hint
            ]
            data.append(data_line)

        pdf.table(
            data,
            columns=[None, None, None, 2.5 * cm, 2.5 * cm],
            style=style,
        )

        pdf.generate()
        result.seek(0)
        return result
