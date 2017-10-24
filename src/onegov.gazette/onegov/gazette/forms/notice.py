from datetime import date
from datetime import datetime
from onegov.form import Form
from onegov.gazette import _
from onegov.gazette.fields import MultiCheckboxField
from onegov.gazette.fields import SelectField
from onegov.gazette.layout import Layout
from onegov.gazette.models import Category
from onegov.quill import QuillField
from wtforms import BooleanField
from wtforms import StringField
from wtforms.validators import InputRequired


class NoticeForm(Form):

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

    at_cost = BooleanField(
        label=_("Liable to pay costs")
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
        principal = self.request.app.principal
        session = self.request.app.session()

        # populate organization
        self.organization.choices = list(principal.organizations.items())
        self.organization.choices.insert(
            0, ('', self.request.translate(_("Select one")))
        )

        # populate categories
        query = session.query(Category.name, Category.title)
        query = query.filter(Category.active == True)
        query = query.order_by(Category.order)
        self.category.choices = query.all()

        # populate issues
        self.issues.choices = []
        layout = Layout(None, self.request)
        today = date.today()
        now = datetime.utcnow()
        publisher = self.request.is_private(self.model)
        for issue_date, issue in principal.issues_by_date.items():
            deadline = principal.issues[issue.year][issue.number].deadline
            if (
                (publisher and today < issue_date) or
                (not publisher and now < deadline)
            ):
                self.issues.choices.append((
                    str(issue),
                    layout.format_issue(
                        issue, date_format='date_with_weekday'
                    )
                ))
                if now >= deadline:
                    self.issues.render_kw['data-hot-issue'] = str(issue)

        # translate the string of the mutli select field
        self.issues.translate(self.request)

    def update_model(self, model):
        model.title = self.title.data
        model.organization_id = self.organization.data
        model.category_id = self.category.data
        model.text = self.text.data
        model.at_cost = self.at_cost.data
        model.issues = self.issues.data

        principal = self.request.app.principal
        session = self.request.app.session()
        model.apply_meta(principal, session)

    def apply_model(self, model):
        self.title.data = model.title
        self.organization.data = model.organization_id
        self.category.data = model.category_id
        self.text.data = model.text
        self.at_cost.data = model.at_cost
        self.issues.data = list(model.issues.keys())
