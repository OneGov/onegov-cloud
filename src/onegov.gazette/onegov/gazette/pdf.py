from io import BytesIO
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Organization
from onegov.gazette.models import Category
from onegov.pdf import Pdf as PdfBase
from sqlalchemy.orm import object_session


class Pdf(PdfBase):

    def h(self, title, level=1):
        """ Add a title h1-h3 according to the given level. """

        getattr(self, 'h{}'.format(min(self.level, 3)))(title)

    def unfold_data(self, data, level=2):
        """ Take a nested list of dicts and add it. """

        for item in data:
            title = item.get('title', None)
            if title:
                self.h(title, level)

            notices = item.get('notices', [])
            for notice in notices:
                self.h(title, level + 1)
                self.p_markup(notice[1])

            children = item.get('children', [])
            if children:
                self.unfold_data(children, level + 1)

    @classmethod
    def from_issue(cls, issue, file=None):
        """ Generate a PDF for one issue. """
        # Collect the data
        session = object_session(issue)
        categories = session.query(Category).order_by(Category.order).all()
        roots = session.query(Organization).filter_by(parent_id=None)
        roots = roots.order_by(Organization.order)

        data = []
        for root in roots:
            root_data = []
            # todo: if not root.children
            if root.children:
                for child in root.children:
                    child_data = []
                    for category in categories:
                        notices = session.query(
                            GazetteNotice.title,
                            GazetteNotice.text
                        )
                        notices = notices.filter(
                            GazetteNotice._issues.has_key(issue.name),  # noqa
                            GazetteNotice.state == 'published',
                            GazetteNotice._organizations.has_key(child.name),
                            GazetteNotice._categories.has_key(category.name)
                        )
                        notices = notices.order_by(
                            GazetteNotice._issues.vals()
                        )
                        notices = notices.all()
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
        file = file or BytesIO()
        pdf = cls(file)
        pdf.init_a4_portrait()
        pdf.h1(issue.name)
        pdf.unfold_data(data)
        pdf.generate()

        return file
