from datetime import date
from io import BytesIO
from onegov.pdf import page_fn_footer
from onegov.pdf import page_fn_header_and_footer
from onegov.pdf import Pdf
from reportlab.lib.units import cm


class AgencyPdf(Pdf):

    @classmethod
    def from_agencies(cls, agencies, author, title="", toc=False):
        """ Create an index PDF from a collection of notices. """

        result = BytesIO()
        pdf = cls(
            result,
            title=title,
            created=f"{date.today():%d.%m.%Y}",
            author=author
        )
        pdf.init_a4_portrait(
            page_fn=page_fn_footer,
            page_fn_later=page_fn_header_and_footer
        )
        pdf.h(title)
        pdf.spacer()
        if toc:
            pdf.table_of_contents()
            pdf.pagebreak()
        for agency in agencies:
            pdf.agency(agency)
            pdf.pagebreak()
        pdf.generate()

        result.seek(0)
        return result

    def memberships(self, agency):
        """ Adds the memberships of an agency as table. """

        data = []
        for membership in agency.memberships:
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
                        description.append(getattr(membership.person, field))
            description = ', '.join([part for part in description if part])

            data.append([
                title,
                membership.meta.get('prefix', ''),
                description
            ])

        self.table(data, [5.5 * cm, 0.5 * cm, None])

    def agency(self, agency, level=1, content_so_far=False):
        """ Adds a single agency with the portrait and memberships. """

        if (level < 4) and content_so_far:
            self.pagebreak()
        else:
            self.spacer()

        self.h(agency.title, level)
        self.story[-1].keepWithNext = True

        has_content = False
        if agency.portrait:
            self.mini_html(agency.portrait_html, linkify=True)
            has_content = True

        if agency.memberships.count():
            self.memberships(agency)
            has_content = True

        if agency.organigram_file:
            self.spacer()
            self.image(BytesIO(agency.organigram_file.read()))
            self.spacer()
            has_content = True

        for child in agency.children:
            child_has_content = self.agency(
                child, level + 1, has_content
            )
            has_content = has_content or child_has_content

        return has_content
