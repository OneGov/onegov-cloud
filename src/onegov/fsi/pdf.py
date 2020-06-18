from datetime import date
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.units import cm
from sedate import utcnow

from onegov.fsi import _
from onegov.pdf import Pdf, page_fn_footer, page_fn_header_and_footer


class FsiPdf(Pdf):

    @property
    def page_fn(self):
        return page_fn_footer

    @property
    def page_fn_later(self):
        return page_fn_header_and_footer

    previous_level_context = None
    pass

    @property
    def table_style(self):
        return [
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
        ]

    @classmethod
    def from_subscriptions(cls, collection, layout, title):
        event = layout.model.course_event
        translate = layout.request.translate
        result = BytesIO()
        pdf = cls(
            result,
            title=title,
            created=f"{date.today():%d.%m.%Y}",
        )
        pdf.init_a4_portrait(
            page_fn=pdf.page_fn,
            page_fn_later=pdf.page_fn_later
        )

        pdf.h(title)
        pdf.p(f"{translate(_('Printed'))} "
              f"{layout.format_date(utcnow(), 'date')}")

        pdf.spacer()

        def get_headers():
            headers = ['Attendee', 'Shortcode']
            if not event:
                headers.append('Course Name')
                headers.append('Date')
            headers += ['Course Status', 'Course attended', 'Last info mail']
            return [translate(_(h)) for h in headers]

        def get_row(subscription):
            row = [str(subscription)]
            sent = False
            att = subscription.attendee
            row.append(att and att.source_id or "")

            if not event:
                row.append(event.name)
                row.append(
                    layout.format_date(event.start, 'datetime')
                )
                sent = event.info_template.last_sent

            row.append(
                translate(layout.format_status(event.status)) if event else ""
            )
            row.append(subscription.event_completed and "✔" or "-")
            row.append(sent and layout.format_date(sent, 'date') or '')
            return row

        data = [get_headers()] + sorted([
            get_row(subs) for subs in collection.query()
        ], key=lambda row: row[0])

        pdf.table(
            data,
            columns='even',
            style=pdf.table_style,
        )
        pdf.generate()
        result.seek(0)
        return result

    @classmethod
    def from_audit_collection(cls, collection, layout, title):
        now = utcnow()
        request = layout.request
        refresh_interval = collection.course.refresh_interval
        result = BytesIO()
        pdf = cls(
            result,
            title=title,
            created=f"{date.today():%d.%m.%Y}",
        )
        pdf.init_a4_portrait(
            page_fn=pdf.page_fn,
            page_fn_later=pdf.page_fn_later
        )

        pdf.h(title)
        filter_str = ""
        if collection.organisations:
            orgs = ", ".join(collection.organisations)
            org_title = request.translate(_("Organisations"))
            filter_str = f"{org_title}: {orgs}"

        if collection.letter:
            letter_title = request.translate(_("Letter"))
            letter_title += f" {collection.letter}"

            if filter_str:
                filter_str += f"{filter_str}, {letter_title}"
            else:
                filter_str = letter_title

        if filter_str:
            pdf.h3(filter_str)

        pdf.p(f"{request.translate(_('Printed'))} "
              f"{layout.format_date(now, 'date')}")

        pdf.spacer()

        data = [layout.audit_table_headers]

        green = HexColor('#1be45b')
        orange = HexColor('#f4cb71')
        red = colors.pink

        style = pdf.table_style

        def bgcolor(ix, row, color):
            return 'BACKGROUND', (row, ix), (row, ix), color

        for ix, e in enumerate(collection.query()):
            dt = layout.next_event_date(e.start, refresh_interval)
            if dt:
                if now > dt:
                    next_event_hint = now.year
                    color = red
                else:
                    not_so_fine = (dt.year == now.year and e.event_completed)
                    color = orange if not_so_fine else green
                    next_event_hint = f"{dt.month}/{dt.year}"
            else:
                next_event_hint = now.year
                color = red
            style.append(bgcolor(ix + 1, 4, color))

            data_line = (
                f"{e.last_name}, {e.first_name}",
                e.source_id, layout.format_date(e.start, 'datetime'),
                e.event_completed and "✔" or "-",
                next_event_hint
            )
            data.append(data_line)

        pdf.table(
            data,
            columns=[None, None, None, 1.7 * cm, 2.5 * cm],
            style=style,
        )

        pdf.generate()
        result.seek(0)
        return result
