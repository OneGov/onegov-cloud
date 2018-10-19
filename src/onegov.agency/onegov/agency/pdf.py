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

        fields = agency.meta.get('export_fields', 'role,title').split(',')

        data = []
        for membership in agency.memberships:
            parts = []
            if membership.person:
                for field in fields:
                    parts.append(
                        getattr(membership.person, field, '') or
                        membership.person.meta.get(field, '') or
                        getattr(membership, field, '')
                    )
            data.append([
                membership.title if 'role' in fields else '',
                membership.meta.get('prefix', ''),
                ', '.join([p for p in parts if p])
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
            self.mini_html(agency.portrait, linkify=True)
            has_content = True

        if agency.memberships.count():
            self.memberships(agency)
            has_content = True

        if agency.organigram_file:
            self.spacer()
            self.image(agency.organigram_file)
            self.spacer()
            has_content = True

        for child in agency.children:
            child_has_content = self.agency(
                child, level + 1, has_content
            )
            has_content = has_content or child_has_content

        return has_content
