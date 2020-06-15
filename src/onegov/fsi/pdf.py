from datetime import date
from io import BytesIO

import babel.dates
from reportlab.lib import colors
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

    @staticmethod
    def audit_headers(request, refresh_interval):

        def format_timedelta(timedelta):
            return babel.dates.format_timedelta(
                delta=timedelta,
                locale=request.locale
            )

        title_rows = (
            _("Name"), _("Shortcode"), _("Last Event"), _("Attended"),
            _("Due by (every ${refresh_interval}",
              mapping={'refresh_interval': format_timedelta(refresh_interval)})
        )
        return [request.translate(head) for head in title_rows]

    @classmethod
    def from_audit_collection(cls, request, collection, layout, title):
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
            orgs = " ,".join(collection.organisations)
            org_title = request.translate(_("Organisations"))
            filter_str = f"{org_title}: {orgs}"

        if collection.letter:
            letter_title = request.translate(_("By Letter"))
            letter_title += f" {collection.letter}"

            if filter_str:
                filter_str += f"{filter_str}, {letter_title}"
            else:
                filter_str = letter_title

        if filter_str:
            pdf.h3(filter_str)

        data = [pdf.audit_headers(request, refresh_interval)]
        color_styles = []
        now = utcnow()
        color = colors.green
        next_event_hint = ""

        complete_repr = {None: "", True: "✔", False: "✘"}

        def tcolor(ix, row, color):
            return 'TEXTCOLOR', (row, ix), (row, ix), color

        for ix, e in enumerate(collection.query()):
            dt = layout.next_event_date(e.start, refresh_interval)

            if dt:
                next_event_hint = f"{dt.month}/{dt.year}"
                if now > dt:
                    color = colors.red
                    next_event_hint = now.year
                elif dt.year == now.year:
                    color = colors.orange
                color_styles.append(tcolor(ix, 4, color))

            data_line = (
                f"{e.last_name}, {e.first_name}",
                e.source_id, layout.format_date(e.start, 'datetime'),
                complete_repr[e.event_completed],
                next_event_hint
            )
            data.append(data_line)

        style = [('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                 ('ALIGN', (3, 0), (4, -1), 'CENTER')]

        print(color_styles)
        pdf.table(
            data,
            columns=[None, None, None, 1.7 * cm, None],
            style=style + color_styles
        )
        pdf.generate()
        result.seek(0)
        return result
