from copy import deepcopy
from io import BytesIO
from onegov.gazette import _
from onegov.gazette.layout import Layout
from onegov.gazette.models import Category
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Organization
from onegov.pdf import page_fn_footer
from onegov.pdf import page_fn_header_and_footer
from onegov.pdf import Pdf as PdfBase


class Pdf(PdfBase):

    def adjust_style(self, font_size=10):
        """ Adds styles for notices. """

        super(Pdf, self).adjust_style(font_size)

        self.style.title = deepcopy(self.style.normal)
        self.style.title.fontSize = 2.25 * self.style.fontSize
        self.style.title.leading = 1.2 * self.style.title.fontSize
        self.style.title.spaceBefore = 0
        self.style.title.spaceAfter = 0.67 * self.style.title.fontSize

        self.style.h_notice = deepcopy(self.style.normal)
        self.style.h_notice.fontSize = 1.125 * self.style.fontSize
        self.style.h_notice.spaceBefore = 1.275 * self.style.h_notice.fontSize
        self.style.h_notice.spaceAfter = 0.275 * self.style.h_notice.fontSize

        self.style.paragraph.spaceAfter = 0.675 * self.style.paragraph.fontSize
        self.style.paragraph.leading = 1.275 * self.style.paragraph.fontSize

        self.style.ul_bullet = '-'
        self.style.li.spaceAfter = 0.275 * self.style.li.fontSize
        self.style.li.leading = 1.275 * self.style.li.fontSize

    def h(self, title, level=0):
        """ Adds a title according to the given level. """

        if not level:
            self.p_markup(title, self.style.title)
        else:
            getattr(self, 'h{}'.format(min(level, 4)))(title)

    def unfold_data(self, data, level=1):
        """ Take a nested list of dicts and add it. """

        for item in data:
            title = item.get('title', None)
            if title:
                self.h(title, level)
                self.story[-1].keepWithNext = True

            notices = item.get('notices', [])
            for notice in notices:
                self.p_markup(
                    '<b>{}</b> <i><font size="{}">{}</font></i>'.format(
                        notice[0],
                        0.875 * self.style.h_notice.fontSize,
                        notice[2]
                    ),
                    self.style.h_notice
                )
                self.story[-1].keepWithNext = True
                self.mini_html(notice[1])

            children = item.get('children', [])
            if children:
                self.unfold_data(children, level + 1)

    @staticmethod
    def query_notices(session, issue, organization, category):
        """ Queries all notices with the given values, ordered by publication
        number.

        """

        notices = session.query(
            GazetteNotice.title,
            GazetteNotice.text,
            GazetteNotice._issues[issue]
        )
        notices = notices.filter(
            GazetteNotice._issues.has_key(issue),  # noqa
            GazetteNotice.state == 'published',
            GazetteNotice._organizations.has_key(organization),
            GazetteNotice._categories.has_key(category)
        )
        notices = notices.order_by(
            GazetteNotice._issues[issue]
        )
        return notices.all()

    @classmethod
    def from_issue(cls, issue, request, file=None):
        """ Generate a PDF for one issue. """

        # Collect the data
        data = []

        session = request.app.session()

        used_categories = session.query(GazetteNotice._categories.keys())
        used_categories = used_categories.filter(
            GazetteNotice._issues.has_key(issue.name),  # noqa
            GazetteNotice.state == 'published',
        )
        used_categories = [cat[0][0] for cat in used_categories]

        used_organizations = session.query(GazetteNotice._organizations.keys())
        used_organizations = used_organizations.filter(
            GazetteNotice._issues.has_key(issue.name),  # noqa
            GazetteNotice.state == 'published',
        )
        used_organizations = [cat[0][0] for cat in used_organizations]

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
                                'children': child_data
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

        file = file or BytesIO()
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
        pdf.unfold_data(data)
        pdf.generate()

        file.seek(0)

        return file
