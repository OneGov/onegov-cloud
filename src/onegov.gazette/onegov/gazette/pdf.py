from copy import deepcopy
from io import BytesIO
from onegov.gazette import _
from onegov.gazette.models import IssueName
from onegov.gazette.layout import Layout
from onegov.gazette.models import Category
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Organization
from onegov.pdf import page_fn_footer
from onegov.pdf import page_fn_header_and_footer
from onegov.pdf import Pdf as PdfBase
from pdfdocument.document import MarkupParagraph


class Pdf(PdfBase):

    def adjust_style(self, font_size=10):
        """ Adds styles for notices. """

        super(Pdf, self).adjust_style(font_size)

        self.style.title = deepcopy(self.style.normal)
        self.style.title.fontSize = 2.25 * self.style.fontSize
        self.style.title.leading = 1.2 * self.style.title.fontSize
        self.style.title.spaceBefore = 0
        self.style.title.spaceAfter = 0.67 * self.style.title.fontSize

        self.style.h_notice = deepcopy(self.style.bold)
        self.style.h_notice.fontSize = 1.125 * self.style.fontSize
        self.style.table_h_notice = self.style.table + (
            ('TOPPADDING', (0, 0), (0, 0), 2),
        )

        self.style.paragraph.spaceAfter = 0.675 * self.style.paragraph.fontSize
        self.style.paragraph.leading = 1.275 * self.style.paragraph.fontSize

        self.style.ul.bullet = '-'
        self.style.li.spaceAfter = 0.275 * self.style.li.fontSize
        self.style.li.leading = 1.275 * self.style.li.fontSize


class IndexPdf(Pdf):

    def adjust_style(self, font_size=10):
        """ Adds styles for notices. """

        super(IndexPdf, self).adjust_style(font_size)

        self.style.index = deepcopy(self.style.normal)
        self.style.index.firstLineIndent = -2 * self.style.index.fontSize
        self.style.index.leftIndent = 2 * self.style.index.fontSize

    def category_index(self, notices):
        """ Adds a category index. """

        last_title = None
        categories = notices.session.query(Category)
        if notices.categories:
            categories = categories.filter(Category.id.in_(notices.categories))
        categories = categories.order_by(Category.title)
        for category in categories:
            numbers = []
            query = notices.query().with_entities(GazetteNotice._issues)
            query = query.filter(
                GazetteNotice._categories.has_key(category.name)  # noqa
            )
            for issues in query:
                numbers.extend([(
                    IssueName.from_string(name).year,
                    IssueName.from_string(name).number,
                    int(number)
                ) for name, number in issues[0].items() if number])
            numbers = ', '.join([
                f'{year}-{issue}-{number}'
                for year, issue, number in sorted(set(numbers))
            ])
            if numbers:
                title = category.title
                if not last_title or last_title[0] != title[0]:
                    self.h3(category.title[0])
                last_title = category.title
                self.p_markup(
                    f'{title}&nbsp;&nbsp;<i>{numbers}</i>',
                    style=self.style.index
                )

    def organization_index(self, notices):
        """ Adds an organization index. """

        last_title = None
        organizations = notices.session.query(Organization)
        if notices.organizations:
            organizations = organizations.filter(
                Organization.id.in_(notices.organizations)
            )
        organizations = organizations.order_by(Organization.title)
        for organization in organizations:
            numbers = []
            query = notices.query().with_entities(GazetteNotice._issues)
            query = query.filter(
                GazetteNotice._organizations.has_key(organization.name)  # noqa
            )
            for issues in query:
                numbers.extend([(
                    IssueName.from_string(name).year,
                    IssueName.from_string(name).number,
                    int(number)
                ) for name, number in issues[0].items() if number])
            numbers = ', '.join([
                f'{year}-{issue}-{number}'
                for year, issue, number in sorted(set(numbers))
            ])
            if numbers:
                title = organization.title
                if not last_title or last_title[0] != title[0]:
                    self.h3(organization.title[0])
                last_title = organization.title
                self.p_markup(
                    f'{title}&nbsp;&nbsp;<i>{numbers}</i>',
                    style=self.style.index
                )

    @classmethod
    def from_notices(cls, notices, request):
        """ Create an index PDF from a collection of notices. """

        title = request.translate(_("Gazette"))
        result = BytesIO()
        pdf = cls(
            result,
            title=title,
            author=request.app.principal.name
        )
        pdf.init_a4_portrait(
            page_fn=page_fn_footer,
            page_fn_later=page_fn_header_and_footer
        )
        pdf.h1(title)
        pdf.h1(request.translate(_("Index")))
        pdf.h2(request.translate(_("Organizations")))
        pdf.organization_index(notices)
        pdf.pagebreak()
        pdf.h2(request.translate(_("Categories")))
        pdf.category_index(notices)
        pdf.generate()

        result.seek(0)
        return result


class NoticesPdf(Pdf):

    def adjust_style(self, font_size=10):
        """ Adds styles for notices. """

        super(NoticesPdf, self).adjust_style(font_size)

        # Indent left everthing to stress the issue number
        self.style.leftIndent = 30
        self.style.title.leftIndent = self.style.leftIndent
        self.style.heading1.leftIndent = self.style.leftIndent
        self.style.heading2.leftIndent = self.style.leftIndent
        self.style.heading3.leftIndent = self.style.leftIndent
        self.style.heading4.leftIndent = self.style.leftIndent
        self.style.paragraph.leftIndent = self.style.leftIndent
        self.style.ol.leftIndent = self.style.leftIndent
        self.style.ul.leftIndent = self.style.leftIndent

    def notice(self, notice, layout, publication_number='xxx'):
        """ Adds an official notice. """

        self.table(
            [[
                MarkupParagraph(publication_number, self.style.normal),
                MarkupParagraph(notice.title, self.style.h_notice)
            ]],
            [self.style.leftIndent, None],
            style=self.style.table_h_notice
        )
        self.story[-1].keepWithNext = True
        self.mini_html(notice.text)
        if notice.author_place and notice.author_date:
            self.story[-1].keepWithNext = True
            self.mini_html(
                "{}, {}<br>{}".format(
                    notice.author_place,
                    layout.format_date(
                        notice.author_date, 'date_long'
                    ),
                    notice.author_name
                )
            )
        for file in notice.files:
            self.pdf(file.reference.file)

    @classmethod
    def from_notice(cls, notice, request):
        """ Create a PDF from a single notice. """

        layout = Layout(None, request)
        result = BytesIO()
        pdf = cls(
            result,
            author=request.app.principal.name
        )
        pdf.init_a4_portrait(
            page_fn=page_fn_footer,
            page_fn_later=page_fn_header_and_footer
        )

        pdf.spacer()
        pdf.notice(notice, layout)
        pdf.generate()

        result.seek(0)
        return result

    @classmethod
    def from_notices(cls, notices, request):
        """ Create a PDF from a collection of notices. """

        layout = Layout(None, request)
        result = BytesIO()
        pdf = cls(
            result,
            author=request.app.principal.name
        )

        pdf.init_a4_portrait(
            page_fn=page_fn_footer,
            page_fn_later=page_fn_header_and_footer
        )
        for notice in notices.query():
            pdf.spacer()
            pdf.notice(notice, layout)
        pdf.generate()

        result.seek(0)
        return result


class IssuePdf(NoticesPdf):
    """ A PDF containing all the notices of a single issue.

    Generating this PDF automatically assigns publication numbers!

    """

    def h(self, title, level=0):
        """ Adds a title according to the given level. """

        if not level:
            self.p_markup(title, self.style.title)
        else:
            getattr(self, 'h{}'.format(min(level, 4)))(title)

    def unfold_data(
        self, session, layout, issue, data, publication_number, level=1
    ):
        """ Take a nested list of dicts and add it. """

        for item in data:
            title = item.get('title', None)
            if title:
                self.h(title, level)
                self.story[-1].keepWithNext = True

            notices = item.get('notices', [])
            for id_ in notices:
                notice = session.query(GazetteNotice).filter_by(id=id_).one()
                notice.set_publication_number(issue, publication_number)
                self.notice(notice, layout, publication_number)
                publication_number = publication_number + 1

            children = item.get('children', [])
            if children:
                publication_number = self.unfold_data(
                    session, layout, issue, children, publication_number,
                    level + 1
                )

            if item.get('break_after', False):
                self.pagebreak()

        return publication_number

    @staticmethod
    def query_notices(session, issue, organization, category):
        """ Queries all notices with the given values, ordered by publication
        number.

        """

        notices = session.query(
            GazetteNotice.id
        )
        notices = notices.filter(
            GazetteNotice._issues.has_key(issue),  # noqa
            GazetteNotice.state == 'published',
            GazetteNotice._organizations.has_key(organization),
            GazetteNotice._categories.has_key(category)
        )
        notices = notices.order_by(
            GazetteNotice._issues[issue],
            GazetteNotice.title
        )
        return [notice[0] for notice in notices]

    @classmethod
    def from_issue(cls, issue, request, first_publication_number):
        """ Generate a PDF for one issue.

        Uses the given number as a starting point for the publication numbers.

        """

        # Collect the data
        data = []

        session = request.session

        used_categories = session.query(GazetteNotice._categories.keys())
        used_categories = used_categories.filter(
            GazetteNotice._issues.has_key(issue.name),  # noqa
            GazetteNotice.state == 'published',
        )
        used_categories = [c[0][0] for c in used_categories if c[0]]

        used_organizations = session.query(GazetteNotice._organizations.keys())
        used_organizations = used_organizations.filter(
            GazetteNotice._issues.has_key(issue.name),  # noqa
            GazetteNotice.state == 'published',
        )
        used_organizations = [o[0][0] for o in used_organizations if o[0]]

        if used_categories and used_organizations:
            categories = session.query(Category)
            categories = categories.filter(Category.name.in_(used_categories))
            categories = categories.order_by(Category.order).all()

            roots = session.query(Organization).filter_by(parent_id=None)
            roots = roots.order_by(Organization.order)

            for root in roots:
                root_data = []
                if not root.children:
                    for category in categories:
                        notices = cls.query_notices(
                            session, issue.name, root.name, category.name
                        )
                        if notices:
                            root_data.append({
                                'title': category.title,
                                'notices': notices
                            })
                else:
                    for child in root.children:
                        if child.name not in used_organizations:
                            continue
                        child_data = []
                        for category in categories:
                            notices = cls.query_notices(
                                session, issue.name, child.name, category.name
                            )
                            if notices:
                                child_data.append({
                                    'title': category.title,
                                    'notices': notices
                                })
                        if child_data:
                            root_data.append({
                                'title': child.title,
                                'children': child_data,
                                'break_after': True if child_data else False
                            })
                if root_data:
                    data.append({
                        'title': root.title,
                        'children': root_data
                    })

        # Generate the PDF
        layout = Layout(None, request)
        title = '{} {}'.format(
            request.translate(_("Gazette")),
            layout.format_issue(issue, date_format='date')
        )

        file = BytesIO()
        pdf = cls(
            file,
            title=title,
            author=request.app.principal.name
        )
        pdf.init_a4_portrait(
            page_fn=page_fn_footer,
            page_fn_later=page_fn_header_and_footer
        )
        pdf.h(title)
        pdf.unfold_data(
            session, layout, issue.name, data, first_publication_number
        )
        pdf.generate()

        file.seek(0)

        return file
