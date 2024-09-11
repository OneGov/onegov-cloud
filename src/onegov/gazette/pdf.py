from copy import deepcopy
from io import BytesIO
from onegov.gazette import _
from onegov.gazette.layout import Layout
from onegov.gazette.models import Category
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import IssueName
from onegov.gazette.models import Organization
from onegov.gazette.utils import bool_is
from onegov.pdf import page_fn_footer
from onegov.pdf import page_fn_header_and_footer
from onegov.pdf import page_fn_header_logo_and_footer
from onegov.pdf import Pdf as PdfBase
from pdfdocument.document import MarkupParagraph
from reportlab.platypus.flowables import PageBreak
from sqlalchemy import func


from typing import Any
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.gazette.collections import GazetteNoticeCollection
    from onegov.gazette.models import Issue
    from onegov.gazette.request import GazetteRequest
    from sqlalchemy.orm import Session
    from uuid import UUID


class Pdf(PdfBase):

    def adjust_style(self, font_size: int = 10) -> None:
        """ Adds styles for notices. """

        super().adjust_style(font_size)

        self.style.title = deepcopy(self.style.normal)
        self.style.title.fontSize = 2.25 * self.style.fontSize
        self.style.title.leading = 1.2 * self.style.title.fontSize
        self.style.title.spaceBefore = 0
        self.style.title.spaceAfter = 0.67 * self.style.title.fontSize

        self.style.h_notice = deepcopy(self.style.bold)
        self.style.h_notice.fontSize = 1.125 * self.style.fontSize
        self.style.table_h_notice = (
            *self.style.table,
            ('TOPPADDING', (0, 0), (0, 0), 2)
        )

        self.style.paragraph.spaceAfter = 0.675 * self.style.paragraph.fontSize
        self.style.paragraph.leading = 1.275 * self.style.paragraph.fontSize

        self.style.ul.bullet = '-'
        self.style.li.spaceAfter = 0.275 * self.style.li.fontSize
        self.style.li.leading = 1.275 * self.style.li.fontSize


class IndexPdf(Pdf):

    def adjust_style(self, font_size: int = 10) -> None:
        """ Adds styles for notices. """

        super().adjust_style(font_size)

        self.style.index = deepcopy(self.style.normal)
        self.style.index.firstLineIndent = -2 * self.style.index.fontSize
        self.style.index.leftIndent = 2 * self.style.index.fontSize

    def category_index(self, notices: 'GazetteNoticeCollection') -> None:
        """ Adds a category index. """

        last_title: str | None = None
        categories = notices.session.query(Category)
        if notices.categories:
            categories = categories.filter(Category.id.in_(notices.categories))
        categories = categories.order_by(Category.title)
        for category in categories:
            numbers = []
            query = notices.query().with_entities(GazetteNotice._issues)
            query = query.filter(
                GazetteNotice._categories.has_key(category.name)  # type:ignore
            )
            for issues in query:
                numbers.extend([(
                    IssueName.from_string(name).year,
                    IssueName.from_string(name).number,
                    int(number)
                ) for name, number in issues[0].items() if number])
            formatted_numbers = ', '.join(
                f'{year}-{issue}-{number}'
                for year, issue, number in sorted(set(numbers))
            )
            if formatted_numbers:
                title = category.title
                if not last_title or last_title[0] != title[0]:
                    self.h3(category.title[0])
                last_title = category.title
                self.p_markup(
                    f'{title}&nbsp;&nbsp;<i>{formatted_numbers}</i>',
                    style=self.style.index
                )

    def organization_index(self, notices: 'GazetteNoticeCollection') -> None:
        """ Adds an organization index. """

        last_title: str | None = None
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
                GazetteNotice._organizations.has_key(  # type:ignore
                    organization.name
                )
            )
            for issues in query:
                numbers.extend([(
                    IssueName.from_string(name).year,
                    IssueName.from_string(name).number,
                    int(number)
                ) for name, number in issues[0].items() if number])
            formatted_numbers = ', '.join(
                f'{year}-{issue}-{number}'
                for year, issue, number in sorted(set(numbers))
            )
            if formatted_numbers:
                title = organization.title
                if not last_title or last_title[0] != title[0]:
                    self.h3(organization.title[0])
                last_title = organization.title
                self.p_markup(
                    f'{title}&nbsp;&nbsp;<i>{formatted_numbers}</i>',
                    style=self.style.index
                )

    @classmethod
    def from_notices(
        cls,
        notices: 'GazetteNoticeCollection',
        request: 'GazetteRequest'
    ) -> BytesIO:
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

    def adjust_style(self, font_size: int = 10) -> None:
        """ Adds styles for notices. """

        super().adjust_style(font_size)

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

    def notice(
        self,
        notice: GazetteNotice,
        layout: Layout,
        publication_number: int | str = 'xxx'
    ) -> None:
        """ Adds an official notice. """

        if isinstance(publication_number, int):
            publication_number = str(publication_number)

        self.table(
            [[
                MarkupParagraph(publication_number, self.style.normal),
                MarkupParagraph(notice.title, self.style.h_notice)
            ]],
            [self.style.leftIndent, None],
            style=self.style.table_h_notice
        )
        self.story[-1].keepWithNext = True
        self.mini_html(notice.text or '')
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
    def from_notice(
        cls,
        notice: GazetteNotice,
        request: 'GazetteRequest'
    ) -> BytesIO:
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
    def from_notices(
        cls,
        notices: 'GazetteNoticeCollection',
        request: 'GazetteRequest'
    ) -> BytesIO:
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

    Allows to automatically assign publication numbers when generating the PDF.

    """

    def h(self, title: str, level: int = 0) -> None:
        """ Adds a title according to the given level. """

        if not level:
            self.p_markup(title, self.style.title)
        else:
            getattr(self, f'h{min(level, 4)}')(title)

    def notice(
        self,
        notice: GazetteNotice,
        layout: Layout,
        publication_number: int | str = 'xxx'
    ) -> None:
        """ Adds an official notice. Hides the content if it is print only. """

        if notice.print_only:
            if isinstance(publication_number, int):
                publication_number = str(publication_number)

            title = layout.request.translate(_(
                "This official notice is only available in the print version."
            ))
            self.table(
                [[
                    MarkupParagraph(publication_number, self.style.normal),
                    MarkupParagraph(f'<i>{title}</i>', self.style.normal)
                ]],
                [self.style.leftIndent, None],
                style=self.style.table_h_notice
            )
        else:
            super().notice(notice, layout, publication_number)

    def excluded_notices_note(
        self,
        number: int,
        request: 'GazetteRequest'
    ) -> None:
        """ Adds a paragraph with the number of excluded (print only) notices.

        """

        note = _(
            "The electronic official gazette is available at "
            "www.amtsblattzug.ch."
        )
        self.p_markup(request.translate(note), style=self.style.paragraph)

        if number:
            note = _(
                "${number} publication(s) with particularly sensitive data "
                "are not available online. They are available in paper form "
                "from the State Chancellery, Seestrasse 2, 6300 Zug, or can "
                "be subscribed to at amtsblatt@zg.ch.",
                mapping={'number': number}
            )
            self.p_markup(request.translate(note), style=self.style.paragraph)

    def unfold_data(
        self,
        session: 'Session',
        layout: Layout,
        issue: str,
        data: list[dict[str, Any]],
        publication_number: int | None,
        level: int = 1
    ) -> int | None:
        """ Take a nested list of dicts and add it. """

        for item in data:
            title = item.get('title', None)
            if title:
                self.h(title, level)
                self.story[-1].keepWithNext = True

            notices = item.get('notices', [])
            for id_ in notices:
                notice = session.query(GazetteNotice).filter_by(id=id_).one()
                if publication_number is None:
                    self.notice(notice, layout, notice.issues[issue] or 'xxx')
                else:
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
    def query_notices(
        session: 'Session',
        issue: str,
        organization: str,
        category: str
    ) -> list['UUID']:
        """ Queries all notices with the given values, ordered by publication
        number.

        """

        notices = session.query(
            GazetteNotice.id
        )
        notices = notices.filter(
            GazetteNotice._issues.has_key(issue),  # type:ignore
            GazetteNotice.state == 'published',
            GazetteNotice._organizations.has_key(organization),  # type:ignore
            GazetteNotice._categories.has_key(category)  # type:ignore
        )
        notices = notices.order_by(
            GazetteNotice._issues[issue],
            GazetteNotice.title
        )
        return [notice for notice, in notices]

    @classmethod
    def query_used_categories(
        cls,
        session: 'Session',
        issue: 'Issue'
    ) -> set[str]:

        query = session.query(GazetteNotice._categories.keys())  # type:ignore
        query = query.filter(
            GazetteNotice._issues.has_key(issue.name),  # type:ignore
            GazetteNotice.state == 'published',
        )
        return {keys[0] for keys, in query if keys}

    @classmethod
    def query_used_organizations(
        cls,
        session: 'Session',
        issue: 'Issue'
    ) -> set[str]:

        query = session.query(
            GazetteNotice._organizations.keys()  # type:ignore
        )
        query = query.filter(
            GazetteNotice._issues.has_key(issue.name),  # type:ignore
            GazetteNotice.state == 'published',
        )
        return {keys[0] for keys, in query if keys}

    @classmethod
    def query_excluded_notices_count(
        cls,
        session: 'Session',
        issue: 'Issue'
    ) -> int:
        query = session.query(func.count(GazetteNotice.id))
        query = query.filter(
            GazetteNotice._issues.has_key(issue.name),  # type:ignore
            GazetteNotice.state == 'published',
            bool_is(GazetteNotice.meta['print_only'], True)
        )
        return query.scalar()

    @classmethod
    def from_issue(
        cls,
        issue: 'Issue',
        request: 'GazetteRequest',
        first_publication_number: int | None,
        links: dict[str, str] | None = None
    ) -> BytesIO:
        """ Generate a PDF for one issue.

        Uses `first_publication_number` as a starting point for assigning
        publication numbers. Uses the existing numbers of the notices if None.

        """

        # Collect the data
        data = []
        session = request.session
        used_categories = cls.query_used_categories(session, issue)
        used_organizations = cls.query_used_organizations(session, issue)
        excluded_notices = cls.query_excluded_notices_count(session, issue)
        if used_categories and used_organizations:
            categories_q = session.query(Category)
            categories_q = categories_q.filter(
                Category.name.in_(used_categories)
            )
            categories = categories_q.order_by(Category.order).all()

            roots = session.query(Organization).filter_by(parent_id=None)
            roots = roots.order_by(Organization.order)

            for root in roots:
                root_data: list[dict[str, Any]] = []
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
            author=request.app.principal.name,
            logo=request.app.logo_for_pdf
        )
        pdf.init_a4_portrait(
            page_fn=page_fn_header_logo_and_footer,
            page_fn_later=page_fn_header_and_footer
        )
        pdf.h(title)
        pdf.excluded_notices_note(excluded_notices, request)
        pdf.unfold_data(
            session, layout, issue.name, data, first_publication_number
        )

        # add a final page with links
        if links:

            if not isinstance(pdf.story[-1], PageBreak):
                pdf.pagebreak()

            pdf.h2(request.translate(_("Additional Links")))

            html = '\n'.join(
                f'<p><b>{title}</b><br><a href="{url}">{url}</a></p>'
                for url, title in links.items()
            )
            pdf.mini_html(html)

        pdf.generate()

        file.seek(0)

        return file


class IssuePrintOnlyPdf(IssuePdf):
    """ A PDF containing all the print only notices of a single issue.

    Generating this PDF does NOT assigns publication numbers!

    """

    def notice(
        self,
        notice: GazetteNotice,
        layout: Layout,
        publication_number: str | int = 'xxx'
    ) -> None:
        """ Adds an official notice. """

        if notice.print_only:
            # we skip the overriden implementation in IssuePdf
            super(IssuePdf, self).notice(notice, layout, publication_number)

    def excluded_notices_note(
        self,
        number: int,
        request: 'GazetteRequest'
    ) -> None:
        """ Adds a paragraph with the number of excluded (print only) notices.

        """

        if number:
            note = _(
                "${number} publication(s) with particularly sensitive data "
                "according to BGS 152.3 §7 Abs. 2.",
                mapping={'number': number}
            )
            self.p_markup(request.translate(note), style=self.style.paragraph)

        note = _(
            "The electronic official gazette is available at "
            "www.amtsblattzug.ch."
        )
        self.p_markup(request.translate(note), style=self.style.paragraph)

    @staticmethod
    def query_notices(
        session: 'Session',
        issue: str,
        organization: str,
        category: str
    ) -> list['UUID']:
        """ Queries all notices with the given values, ordered by publication
        number.

        """

        notices = session.query(
            GazetteNotice.id
        )
        notices = notices.filter(
            GazetteNotice._issues.has_key(issue),  # type:ignore
            GazetteNotice.state == 'published',
            GazetteNotice._organizations.has_key(organization),  # type:ignore
            GazetteNotice._categories.has_key(category),  # type:ignore
            bool_is(GazetteNotice.meta['print_only'], True)
        )
        notices = notices.order_by(
            GazetteNotice._issues[issue],
            GazetteNotice.title
        )
        return [notice for notice, in notices]

    @classmethod
    def query_used_categories(
        cls,
        session: 'Session',
        issue: 'Issue'
    ) -> set[str]:

        query = session.query(GazetteNotice._categories.keys())  # type:ignore
        query = query.filter(
            GazetteNotice._issues.has_key(issue.name),  # type:ignore
            GazetteNotice.state == 'published',
            bool_is(GazetteNotice.meta['print_only'], True)
        )
        return {keys[0] for keys, in query if keys}

    @classmethod
    def query_used_organizations(
        cls,
        session: 'Session',
        issue: 'Issue'
    ) -> set[str]:

        query = session.query(
            GazetteNotice._organizations.keys()  # type:ignore
        )
        query = query.filter(
            GazetteNotice._issues.has_key(issue.name),  # type:ignore
            GazetteNotice.state == 'published',
            bool_is(GazetteNotice.meta['print_only'], True)
        )
        return {keys[0] for keys, in query if keys}

    @classmethod
    def from_issue(  # type:ignore[override]
        cls,
        issue: 'Issue',
        request: 'GazetteRequest'
    ) -> BytesIO:
        """ Generate a PDF for one issue. """

        return super().from_issue(issue, request, None)
