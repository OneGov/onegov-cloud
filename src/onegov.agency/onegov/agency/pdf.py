from datetime import date
from io import BytesIO
from onegov.core.utils import module_path
from onegov.pdf import page_fn_footer
from onegov.pdf import page_fn_header_and_footer
from onegov.pdf import page_fn_header_logo
from onegov.pdf import Pdf
from os import path
from reportlab.lib.units import cm


class AgencyPdfDefault(Pdf):
    """ A standard PDF of an agency. """

    @property
    def page_fn(self):
        return page_fn_footer

    @property
    def page_fn_later(self):
        return page_fn_header_and_footer

    @classmethod
    def from_agencies(cls, agencies, title, toc, exclude):
        """ Create an index PDF from a collection of notices. """

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
        pdf.spacer()
        pdf.spacer()
        pdf.h(title)
        pdf.spacer()
        if toc:
            pdf.table_of_contents()
            pdf.pagebreak()
        for agency in agencies:
            if agency.is_hidden_from_public:
                continue
            pdf.agency(agency, exclude, skip_title=title == agency.title)
            pdf.pagebreak()
        pdf.generate()

        result.seek(0)
        return result

    def memberships(self, agency, exclude):
        """ Adds the memberships of an agency as table. """

        data = []
        for membership in agency.memberships:
            if (
                membership.is_hidden_from_public
                or membership.person.is_hidden_from_public
            ):
                continue

            title = ''
            if 'membership.title' in agency.export_fields:
                title = membership.title

            description = []
            if membership.person:
                for field in agency.export_fields or []:
                    if field == 'membership.title':
                        continue
                    if field.startswith('membership.'):
                        field = field.split('membership.')[1]
                        description.append(getattr(membership, field))
                    if field.startswith('person.'):
                        field = field.split('person.')[1]
                        if field in exclude:
                            continue
                        description.append(getattr(membership.person, field))
            description = ', '.join([part for part in description if part])

            data.append([
                title,
                membership.meta.get('prefix', ''),
                description
            ])

        if data:
            self.table(data, [5.5 * cm, 0.5 * cm, None])

    def agency(self, agency, exclude, level=1, content_so_far=False,
               skip_title=False):
        """ Adds a single agency with the portrait and memberships. """

        if (level < 4) and content_so_far:
            self.pagebreak()
        else:
            self.spacer()

        if not skip_title:
            self.h(agency.title, level)
            self.story[-1].keepWithNext = True

        has_content = False
        if agency.portrait:
            self.mini_html(agency.portrait_html, linkify=True)
            has_content = True

        if agency.memberships.count():
            self.memberships(agency, exclude)
            has_content = True

        if agency.organigram_file:
            self.spacer()
            self.image(BytesIO(agency.organigram_file.read()))
            self.spacer()
            has_content = True

        for child in agency.children:
            if child.is_hidden_from_public:
                continue
            child_has_content = self.agency(
                child, exclude, level + 1, has_content
            )
            has_content = has_content or child_has_content

        return has_content


class AgencyPdfZg(AgencyPdfDefault):
    """ A PDF with the CI of the canton of ZG. """

    @staticmethod
    def page_fn_footer(canvas, doc):
        """ A footer with the title and print date on the left and the page
        numbers on the right.

        """

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
            f'{canvas._pageNumber}'
        )
        canvas.restoreState()

    @property
    def page_fn(self):
        return page_fn_header_logo

    @property
    def page_fn_later(self):
        return self.page_fn_footer

    def __init__(self, *args, **kwargs):
        filename = path.join(
            module_path('onegov.agency', 'static/logos'),
            'canton-zg-bw.svg'
        )
        with open(filename) as file:
            logo = file.read()
        kwargs['logo'] = logo
        kwargs['author'] = "Kanton Zug"
        super(AgencyPdfDefault, self).__init__(*args, **kwargs)


class AgencyPdfAr(AgencyPdfDefault):
    """ A PDF with the CI of the canton of AR. """

    @staticmethod
    def page_fn_footer(canvas, doc):
        """ A footer with the print date on the left and the page numbers
        on the right.

        """

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
            f'{canvas._pageNumber}'
        )
        canvas.restoreState()

    @staticmethod
    def page_fn_header_logo_and_footer(canvas, doc):
        """ A header with the logo, a footer with the print date and page
        numbers.

        """

        page_fn_header_logo(canvas, doc)
        AgencyPdfAr.page_fn_footer(canvas, doc)

    @staticmethod
    def page_fn_header_and_footer(canvas, doc):
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
    def page_fn(self):
        return self.page_fn_header_logo_and_footer

    @property
    def page_fn_later(self):
        return self.page_fn_header_and_footer

    def __init__(self, *args, **kwargs):
        filename = path.join(
            module_path('onegov.agency', 'static/logos'),
            'canton-ar.svg'
        )
        with open(filename) as file:
            logo = file.read()
        kwargs['logo'] = logo
        kwargs['author'] = "Kanton Appenzell Ausserrhoden"
        super(AgencyPdfDefault, self).__init__(*args, **kwargs)
