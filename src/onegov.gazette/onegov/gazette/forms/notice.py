from datetime import date
from onegov.form import Form
from onegov.gazette import _
from onegov.gazette.fields import MultiCheckboxField
from onegov.gazette.fields import SelectField
from onegov.gazette.layout import Layout
from onegov.gazette.models import Category
from onegov.gazette.models import Issue
from onegov.gazette.models import Organization
from onegov.quill import QuillField
from sedate import utcnow
from wtforms import BooleanField
from wtforms import RadioField
from wtforms import StringField
from wtforms import TextAreaField
from wtforms.validators import InputRequired


class NoticeForm(Form):
    """ Edit an official notice.

    The issues are limited according to the deadline (or the issue date in the
    for publishers) and the categories and organizations are limited to the
    active one.

    """

    title = StringField(
        label=_("Title"),
        validators=[
            InputRequired()
        ]
    )

    organization = SelectField(
        label=_("Organization"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    category = SelectField(
        label=_("Category"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    print_only = BooleanField(
        label=_("Print only"),
        default=False
    )

    at_cost = RadioField(
        label=_("Liable to pay costs"),
        default='no',
        choices=[
            ('no', _("No")),
            ('yes', _("Yes"))
        ]
    )

    billing_address = TextAreaField(
        label=_("Billing address"),
        render_kw={'rows': 3},
        depends_on=('at_cost', 'yes')
    )

    issues = MultiCheckboxField(
        label=_("Issue(s)"),
        choices=[],
        validators=[
            InputRequired()
        ],
        limit=5
    )

    text = QuillField(
        label=_("Text"),
        tags=('strong', 'ol', 'ul'),
        validators=[
            InputRequired()
        ]
    )

    def on_request(self):
        session = self.request.app.session()

        # populate organization (active root elements with no children or
        # active children (but not their parents))
        self.organization.choices = []
        self.organization.choices.append(
            ('', self.request.translate(_("Select one")))
        )
        query = session.query(Organization)
        query = query.filter(Organization.active.is_(True))
        query = query.filter(Organization.parent_id.is_(None))
        query = query.order_by(Organization.order)
        for root in query:
            if root.children:
                for child in root.children:
                    if child.active:
                        self.organization.choices.append(
                            (child.name, child.title)
                        )
            else:
                self.organization.choices.append((root.name, root.title))

        # populate categories
        query = session.query(Category.name, Category.title)
        query = query.filter(Category.active.is_(True))
        query = query.order_by(Category.order)
        self.category.choices = query.all()

        # populate issues
        now = utcnow()
        layout = Layout(None, self.request)

        self.issues.choices = []
        query = session.query(Issue)
        query = query.order_by(Issue.date)
        if self.request.is_private(self.model):
            query = query.filter(date.today() < Issue.date)  # publisher
        else:
            query = query.filter(now < Issue.deadline)  # editor
        for issue in query:
            self.issues.choices.append((
                issue.name,
                layout.format_issue(issue, date_format='date_with_weekday')
            ))
            if now >= issue.deadline:
                self.issues.render_kw['data-hot-issue'] = issue.name

        # translate the string of the mutli select field
        self.issues.translate(self.request)

        # Remove the print only option if not publisher
        if not self.request.is_private(self.model):
            self.delete_field('print_only')

    def update_model(self, model):
        model.title = self.title.data
        model.organization_id = self.organization.data
        model.category_id = self.category.data
        model.text = self.text.data
        model.at_cost = self.at_cost.data == 'yes'
        model.billing_address = self.billing_address.data
        model.issues = self.issues.data
        if self.print_only:
            model.print_only = self.print_only.data

        model.apply_meta(self.request.app.session())

    def apply_model(self, model):
        self.title.data = model.title
        self.organization.data = model.organization_id
        self.category.data = model.category_id
        self.text.data = model.text
        self.at_cost.data = 'yes' if model.at_cost else 'no'
        self.billing_address.data = model.billing_address or ''
        self.issues.data = list(model.issues.keys())
        if self.print_only:
            self.print_only.data = True if model.print_only else False


class UnrestrictedNoticeForm(NoticeForm):
    """ Edit an official notice without limitations on the issues, categories
    and organiaztions.

    Optionally disables the issues (e.g. if the notice is already published).

    """

    def on_request(self):
        session = self.request.app.session()
        layout = Layout(None, self.request)

        def title(item):
            return item.title if item.active else '({})'.format(item.title)

        # populate organization (root elements with no children or children
        # (but not their parents))
        self.organization.choices = []
        self.organization.choices.append(
            ('', self.request.translate(_("Select one")))
        )
        query = session.query(Organization)
        query = query.filter(Organization.parent_id.is_(None))
        query = query.order_by(Organization.order)
        for root in query:
            if root.children:
                for child in root.children:
                    self.organization.choices.append(
                        (child.name, title(child))
                    )
            else:
                self.organization.choices.append((root.name, title(root)))

        # populate categories
        self.category.choices = []
        query = session.query(Category)
        query = query.order_by(Category.order)
        for category in query:
            self.category.choices.append((category.name, title(category)))

        # populate issues
        del self.issues.render_kw['data-limit']
        self.issues.choices = []
        query = session.query(Issue)
        query = query.order_by(Issue.date)
        for issue in query:
            self.issues.choices.append((
                issue.name,
                layout.format_issue(issue, date_format='date_with_weekday')
            ))

        # translate the string of the mutli select field
        self.issues.translate(self.request)

    def disable_issues(self):
        self.issues.validators = []
        self.issues.render_kw['disabled'] = True

    def update_model(self, model):
        model.title = self.title.data
        model.organization_id = self.organization.data
        model.category_id = self.category.data
        model.text = self.text.data
        model.at_cost = self.at_cost.data
        if model.state != 'published':
            model.issues = self.issues.data

        model.apply_meta(self.request.app.session())
