from __future__ import annotations

from datetime import date
from io import BytesIO


from onegov.agency.utils import handle_empty_p_tags
from onegov.core.utils import module_path
from onegov.pdf import page_fn_footer
from onegov.pdf import page_fn_header_and_footer
from onegov.pdf import page_fn_header_logo
from onegov.pdf import Pdf
from onegov.pdf.page_functions import empty_page_fn
from os import path
from reportlab.lib.units import cm


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Callable
    from collections.abc import Collection
    from collections.abc import Iterable
    from onegov.agency.models import ExtendedAgency
    from onegov.pdf.templates import Template
    from reportlab.pdfgen.canvas import Canvas
    from reportlab.platypus.doctemplate import _PageCallback


class AgencyPdfDefault(Pdf):
    """ A standard PDF of an agency. """

    previous_level_context: int | None = None

    @property
    def page_fn(self) -> Callable[[Canvas, Template], None]:
        return page_fn_footer

    @property
    def page_fn_later(self) -> Callable[[Canvas, Template], None]:
        return page_fn_header_and_footer

    @classmethod
    def from_agencies(
        cls,
        agencies: Iterable[ExtendedAgency],
        title: str,
        toc: bool,
        exclude: Collection[str],
        page_break_on_level: int = 1,
        link_color: str | None = None,
        underline_links: bool = False
    ) -> BytesIO:
        """ Create an index PDF from a collection of notices. """

        result = BytesIO()
        pdf = cls(
            result,
            title=title,
            created=f'{date.today():%d.%m.%Y}',
            link_color=link_color or '#00538c',
            underline_links=underline_links
        )
        pdf.init_a4_portrait(
            page_fn=pdf.page_fn,
            page_fn_later=pdf.page_fn_later
        )
        pdf.spacer()
        pdf.spacer()
        pdf.h(title)
        pdf.spacer()
        if toc:
            pdf.table_of_contents()
            pdf.pagebreak()
        for agency in agencies:
            if agency.access == 'private' or not agency.published:
                continue
            pdf.agency(agency, exclude,
                       content_so_far=False,
                       skip_title=title == agency.title,
                       page_break_on_level=page_break_on_level)
        pdf.generate()
        result.seek(0)
        return result

    def memberships(
        self,
        agency: ExtendedAgency,
        exclude: Collection[str]
    ) -> None:
        """ Adds the memberships of an agency as table. """

        data = []
        for membership in agency.memberships:
            if (
                membership.access == 'private'
                or membership.person.access == 'private'
                or not membership.published
                or not membership.person.published
            ):
                continue

            description = []
            first_attribute: str | None = None
            if membership.person:
                for field in agency.export_fields or []:
                    if field.startswith('membership.'):
                        field = field.split('membership.')[1]
                        if not first_attribute:
                            first_attribute = getattr(membership, field)
                        else:
                            description.append(getattr(membership, field))
                    if field.startswith('person.'):
                        field = field.split('person.')[1]
                        if field in exclude:
                            continue
                        if not first_attribute:
                            first_attribute = getattr(membership.person, field)
                        else:
                            description.append(
                                getattr(membership.person, field)
                            )
            description_str = ', '.join(part for part in description if part)

            prefix = membership.meta.get('prefix', '') or ''
            data.append(
                [first_attribute or '', prefix, description_str]
            )

        if data:
            self.table(
                data, [5.5 * cm, 0.5 * cm, None]
            )

    def agency(
        self,
        agency: ExtendedAgency,
        exclude: Collection[str],
        level: int = 1,
        content_so_far: bool = False,
        skip_title: bool = False,
        page_break_on_level: int = 1,
        portrait_last_content: bool = False
    ) -> bool:
        """ Adds a single agency with the portrait and memberships. """
        if (
                self.previous_level_context
                and level <= page_break_on_level
                and self.previous_level_context >= level
        ):
            self.pagebreak()
        else:
            if content_so_far and not portrait_last_content:
                self.spacer()
            if not content_so_far and self.previous_level_context:
                self.keeptogether_index = len(self.story) - 1
            else:
                self.start_keeptogether()

        self.previous_level_context = level

        if not skip_title:
            self.h(agency.title, level)
            self.story[-1].keepWithNext = True

        has_content = False
        portrait_last_content = False
        if agency.portrait and handle_empty_p_tags(agency.portrait):
            self.mini_html(agency.portrait_html, linkify=True)
            has_content = True
            portrait_last_content = True

        if agency.location_address or agency.location_code_city:
            address = agency.location_address
            city = agency.location_code_city
            self.p(address) if address else None
            self.p(city) if city else None
            self.spacer(0.1 * cm)
            has_content = True
            portrait_last_content = False

        if agency.postal_address or agency.postal_code_city:
            address = agency.postal_address
            city = agency.postal_code_city
            self.p(address) if address else None
            self.p(city) if city else None
            self.spacer(0.1 * cm)
            has_content = True
            portrait_last_content = False

        if agency.phone:
            self.p(agency.phone)
            self.spacer(0.1 * cm)
            has_content = True
            portrait_last_content = False

        if agency.email:
            self.p(agency.email)
            self.spacer(0.1 * cm)
            has_content = True
            portrait_last_content = False

        if agency.website:
            web = agency.website.replace('http://', '').replace(
                'https://', '')
            self.p(web)
            self.spacer(0.1 * cm)
            has_content = True
            portrait_last_content = False

        if agency.opening_hours:
            self.p(agency.opening_hours)
            has_content = True
            portrait_last_content = False

        if has_content:
            self.spacer(0.3 * cm)

        if agency.memberships.count():
            self.memberships(agency, exclude)
            has_content = True
            portrait_last_content = False

        if agency.organigram_file:
            self.spacer()
            self.image(BytesIO(agency.organigram_file.read()))
            self.spacer()
            has_content = True
            portrait_last_content = False

        if has_content and hasattr(self, 'keeptogether_index'):
            self.end_keeptogether()

        for child in agency.children:
            if child.access == 'private' or not child.published:
                continue
            child_has_content = self.agency(
                child, exclude, level + 1, has_content,
                page_break_on_level=page_break_on_level,
                portrait_last_content=portrait_last_content
            )
            has_content = has_content or child_has_content

        return has_content


class AgencyPdfZg(AgencyPdfDefault):
    """ A PDF with the CI of the canton of ZG. """

    @staticmethod
    def page_fn_footer(canvas: Canvas, doc: Template) -> None:
        """ A footer with the title and print date on the left and the page
        numbers on the right.

        """

        assert doc.title is not None
        assert hasattr(doc, 'created')
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(
            doc.leftMargin,
            doc.bottomMargin / 2 + 12,
            doc.title
        )
        canvas.drawString(
            doc.leftMargin,
            doc.bottomMargin / 2,
            f'Druckdatum: {doc.created}'
        )
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            doc.bottomMargin / 2,
            f'{canvas.getPageNumber()}'
        )
        canvas.restoreState()

    @property
    def page_fn(self) -> Callable[[Canvas, Template], None]:
        return page_fn_header_logo

    @property
    def page_fn_later(self) -> Callable[[Canvas, Template], None]:
        return self.page_fn_footer

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        filename = path.join(
            module_path('onegov.agency', 'static/logos'),
            'canton-zg-bw.svg'
        )
        with open(filename) as file:
            logo = file.read()
        kwargs['logo'] = logo
        kwargs['author'] = 'Kanton Zug'
        super().__init__(*args, **kwargs)


class AgencyPdfAr(AgencyPdfDefault):
    """ A PDF with the CI of the canton of AR. """

    @staticmethod
    def page_fn_footer(canvas: Canvas, doc: Template) -> None:
        """ A footer with the print date on the left and the page numbers
        on the right.

        """

        assert hasattr(doc, 'created')
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(
            doc.leftMargin,
            doc.bottomMargin / 2,
            f'Druckdatum: {doc.created}'
        )
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            doc.bottomMargin / 2,
            f'{canvas.getPageNumber()}'
        )
        canvas.restoreState()

    @staticmethod
    def page_fn_header_logo_and_footer(
        canvas: Canvas,
        doc: Template
    ) -> None:
        """ A header with the logo, a footer with the print date and page
        numbers.

        """
        height = .81 * cm
        width = height * 5.72

        assert hasattr(doc, 'logo')
        canvas.saveState()
        canvas.drawImage(
            doc.logo,
            x=doc.leftMargin,
            y=doc.pagesize[1] - 2.35 * cm,
            height=height,
            width=width,
            mask='auto')
        canvas.restoreState()
        AgencyPdfAr.page_fn_footer(canvas, doc)

    @staticmethod
    def page_fn_header_and_footer(canvas: Canvas, doc: Template) -> None:
        """ A header with the title and author, a footer with the print date
        and page numbers.

        """

        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(
            doc.leftMargin,
            doc.pagesize[1] - doc.topMargin * 2 / 3,
            f'{doc.title} {doc.author}'
        )
        canvas.restoreState()

        AgencyPdfAr.page_fn_footer(canvas, doc)

    @property
    def page_fn(self) -> Callable[[Canvas, Template], None]:
        return self.page_fn_header_logo_and_footer

    @property
    def page_fn_later(self) -> Callable[[Canvas, Template], None]:
        return self.page_fn_header_and_footer

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        filename = path.join(
            module_path('onegov.agency', 'static/logos'),
            'canton-ar.png'
        )
        kwargs['logo'] = filename
        kwargs['author'] = 'Kanton Appenzell Ausserrhoden'
        super().__init__(*args, **kwargs)


class AgencyPdfBs(AgencyPdfDefault):
    """
    Consult the styleguide from 2021.

    Page Settings are on page 25:

    Logo position to page margins, left most visual part of the logo:
    - indent 10mm left
    - 10mm beneath top
    - Format A4: The Baslerstab must be 10mm high, total is 17.5mm with the |

    p. 24
    - Font Arial
    - Footer: Arial pt, start approx 12mm beneath bottom margin
    - Regular text Arial 11p

    """
    margin_top = 2.2 * cm
    margin_bottom = 2.4 * cm
    margin_left = 2.2 * cm
    margin_right = 2 * cm
    font_name = 'Helvetica'  # Arial not supported by now
    font_size = 11

    @staticmethod
    def page_fn_header(canvas: Canvas, doc: Template) -> None:
        """ A header with the logo, a footer with the print date and page
        numbers.

        """
        assert hasattr(doc, 'logo')
        height = 1.85 * cm
        width = height * 2.77

        canvas.saveState()
        # 0/0 is bottom left
        canvas.drawImage(
            doc.logo,
            x=1 * cm,
            y=doc.pagesize[1] - (1 + 1.85) * cm,
            height=height,
            width=width,
            mask='auto')
        canvas.restoreState()
        AgencyPdfBs.page_fn_footer(canvas, doc)

    @staticmethod
    def page_fn_footer(canvas: Canvas, doc: Template) -> None:
        assert hasattr(doc, 'created')
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.drawString(
            doc.leftMargin,
            doc.bottomMargin - 1.2 * cm,    # p.24
            f'Druckdatum: {doc.created}'
        )
        canvas.drawRightString(
            doc.pagesize[0] - doc.rightMargin,
            doc.bottomMargin / 2,
            f'{canvas.getPageNumber()}'
        )
        canvas.restoreState()

    @property
    def page_fn(self) -> Callable[[Canvas, Template], None]:
        return self.page_fn_header

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        filename = path.join(
            module_path('onegov.agency', 'static/logos'),
            'canton-bs.png'
        )

        kwargs['logo'] = filename
        kwargs['author'] = 'Kanton Basel-Stadt'

        # These are not set like the frame and the table is indented by the
        # difference of the default margin on init of self.doc and the set
        # margin here. The combination of setting the same margins on the
        # page templates (Frames) and on init made the table aligned with the
        # margins set on init_a4_portrait.
        kwargs['topMargin'] = self.margin_top
        kwargs['topBottom'] = self.margin_bottom

        kwargs['leftMargin'] = self.margin_left
        kwargs['rightMargin'] = self.margin_right

        super(AgencyPdfDefault, self).__init__(*args, **kwargs)

    def init_a4_portrait(
        self,
        page_fn: _PageCallback = empty_page_fn,
        page_fn_later: _PageCallback | None = None,
        **_ignored: object
    ) -> None:
        super().init_a4_portrait(
            page_fn,
            page_fn_later,
            margin_top=self.margin_top,
            margin_bottom=self.margin_bottom,
            margin_left=self.margin_left,
            margin_right=self.margin_right,
            font_size=self.font_size
        )


class AgencyPdfLu(AgencyPdfDefault):
    """
    No hierarchical numbering

    """

    @property
    def page_fn(self) -> Callable[[Canvas, Template], None]:
        return page_fn_header_logo

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        filename = path.join(
            module_path('onegov.agency', 'static/logos'),
            'canton-lu.svg'
        )

        with open(filename) as file:
            logo = file.read()
        kwargs['logo'] = logo
        kwargs['author'] = 'Kanton Luzern'

        kwargs['skip_numbering'] = True
        super(AgencyPdfDefault, self).__init__(*args, **kwargs)
