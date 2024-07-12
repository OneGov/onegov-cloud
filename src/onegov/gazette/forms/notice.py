from datetime import date
from datetime import datetime
from markupsafe import Markup
from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.fields import PhoneNumberField
from onegov.gazette import _
from onegov.gazette.fields import MultiCheckboxField
from onegov.gazette.layout import Layout
from onegov.gazette.models import Category
from onegov.gazette.models import Issue
from onegov.gazette.models import Organization
from onegov.quill.fields import QuillField
from onegov.quill.validators import HtmlDataRequired
from sedate import as_datetime
from sedate import standardize_date
from sedate import utcnow
from wtforms.fields import BooleanField
from wtforms.fields import DateField
from wtforms.fields import RadioField
from wtforms.fields import StringField
from wtforms.fields import TextAreaField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired
from wtforms.validators import Length


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.gazette.models import GazetteNotice
    from onegov.gazette.request import GazetteRequest


class NoticeForm(Form):
    """ Edit an official notice.

    The issues are limited according to the deadline (or the issue date in the
    for publishers) and the categories and organizations are limited to the
    active one.

    """

    request: 'GazetteRequest'

    title = StringField(
        label=_("Title (maximum 60 characters)"),
        validators=[
            InputRequired(),
            DataRequired(),
            Length(max=60)
        ],
        render_kw={'maxlength': 60},
    )

    organization = ChosenSelectField(
        label=_("Organization"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    category = ChosenSelectField(
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
        depends_on=('at_cost', 'yes'),
        validators=[
            InputRequired(),
            DataRequired(),
        ]
    )

    issues = MultiCheckboxField(
        label=_("Issue(s)"),
        choices=[],
        validators=[
            InputRequired()
        ]
    )

    text = QuillField(
        label=_("Text"),
        tags=('strong', 'ol', 'ul'),
        validators=[
            InputRequired(),
            HtmlDataRequired(),
        ]
    )

    author_place = StringField(
        label=_("Place"),
        validators=[
            InputRequired(),
            DataRequired(),
        ]
    )

    author_date = DateField(
        label=_("Date (usually the date of the issue)"),
        validators=[
            InputRequired()
        ]
    )

    phone_number = PhoneNumberField(
        label=_("Phone number for enquiry"),
        description="+41791112233",
    )

    author_name = TextAreaField(
        label=_("Author"),
        validators=[
            InputRequired(),
            DataRequired(),
        ],
        render_kw={'rows': 4},
    )

    @property
    def author_date_utc(self) -> datetime | None:
        if self.author_date.data:
            return standardize_date(as_datetime(self.author_date.data), 'UTC')
        return None

    def on_request(self) -> None:
        session = self.request.session

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
        category_query = session.query(Category.name, Category.title)
        category_query = category_query.filter(Category.active.is_(True))
        category_query = category_query.order_by(Category.order)
        self.category.choices = category_query.all()

        # populate issues
        now = utcnow()
        layout = Layout(None, self.request)

        self.issues.choices = []
        issues_q = session.query(Issue)
        issues_q = issues_q.order_by(Issue.date)
        if self.request.is_private(self.model):
            issues_q = issues_q.filter(date.today() < Issue.date)  # publisher
        else:
            issues_q = issues_q.filter(now < Issue.deadline)  # editor
        for issue in issues_q:
            self.issues.choices.append((
                issue.name,
                layout.format_issue(issue, date_format='date_with_weekday')
            ))
            if issue.deadline is not None and now >= issue.deadline:
                self.issues.render_kw['data-hot-issue'] = issue.name

        # Remove the print only option if not publisher
        if not self.request.is_private(self.model):
            self.delete_field('print_only')

    def update_model(self, model: 'GazetteNotice') -> None:
        assert self.title.data is not None
        model.title = self.title.data
        model.organization_id = self.organization.data
        model.category_id = self.category.data
        model.text = self.text.data
        model.author_place = self.author_place.data
        model.author_date = self.author_date_utc
        model.author_name = self.author_name.data
        model.at_cost = self.at_cost.data == 'yes'
        model.billing_address = self.billing_address.data
        # FIXME: asymmetric property
        model.issues = self.issues.data  # type:ignore[assignment]
        if self.print_only:
            model.print_only = self.print_only.data
        if self.phone_number.data and model.user:
            model.user.phone_number = self.phone_number.formatted_data
        model.apply_meta(self.request.session)

    def apply_model(self, model: 'GazetteNotice') -> None:
        self.title.data = model.title
        self.organization.data = model.organization_id
        self.category.data = model.category_id
        self.text.data = model.text or Markup('')
        self.author_place.data = model.author_place
        self.author_date.data = model.author_date
        self.author_name.data = model.author_name
        self.at_cost.data = 'yes' if model.at_cost else 'no'
        self.billing_address.data = model.billing_address or ''
        self.issues.data = list(model.issues.keys())
        if model.user:
            self.phone_number.data = model.user.phone_number
        if self.print_only:
            self.print_only.data = True if model.print_only else False


class UnrestrictedNoticeForm(NoticeForm):
    """ Edit an official notice without limitations on the issues, categories
    and organiaztions.

    Optionally disables the issues (e.g. if the notice is already published).

    """

    note = TextAreaField(
        label=_("Note"),
        render_kw={'rows': 3},
    )

    def on_request(self) -> None:
        session = self.request.session
        layout = Layout(None, self.request)

        def title(item: Organization | Category) -> str:
            return item.title if item.active else f'({item.title})'

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
        categories_query = session.query(Category)
        categories_query = categories_query.order_by(Category.order)
        for category in categories_query:
            self.category.choices.append((category.name, title(category)))

        # populate issues
        del self.issues.render_kw['data-limit']
        self.issues.choices = []
        issues_query = session.query(Issue)
        issues_query = issues_query.order_by(Issue.date)
        for issue in issues_query:
            self.issues.choices.append((
                issue.name,
                layout.format_issue(issue, date_format='date_with_weekday')
            ))

    def disable_issues(self) -> None:
        self.issues.validators = []
        self.issues.render_kw['disabled'] = True

    def update_model(self, model: 'GazetteNotice') -> None:
        assert self.title.data is not None
        model.title = self.title.data
        model.organization_id = self.organization.data
        model.category_id = self.category.data
        model.text = self.text.data
        model.author_place = self.author_place.data
        model.author_date = self.author_date_utc
        model.author_name = self.author_name.data
        model.at_cost = self.at_cost.data == 'yes'
        model.billing_address = self.billing_address.data
        model.note = self.note.data
        model.print_only = self.print_only.data
        if model.state != 'published':
            model.issues = self.issues.data  # type:ignore[assignment]
        if self.phone_number.data and model.user:
            model.user.phone_number = self.phone_number.formatted_data
        model.apply_meta(self.request.session)

    def apply_model(self, model: 'GazetteNotice') -> None:
        super().apply_model(model)
        self.note.data = model.note
