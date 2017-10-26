from onegov.form import Form
from onegov.gazette import _
from onegov.gazette.models import Organization
from sqlalchemy import cast
from sqlalchemy import String
from wtforms import BooleanField
from wtforms import SelectField
from wtforms import StringField
from wtforms.validators import InputRequired


class OrganizationForm(Form):

    parent = SelectField(
        label=_("Parent Organization"),
        choices=[('', '')]
    )

    title = StringField(
        label=_("Title"),
        validators=[
            InputRequired()
        ]
    )

    active = BooleanField(
        label=_("Active"),
        default=True
    )

    def on_request(self):
        session = self.request.app.session()
        query = session.query(
            cast(Organization.id, String),
            Organization.title
        )
        query = query.filter(Organization.parent_id.is_(None))
        self.parent.choices = query.all()
        self.parent.choices.insert(
            0, ('', self.request.translate(_("- none -")))
        )

    def update_model(self, model):
        model.title = self.title.data
        model.active = self.active.data
        model.parent_id = self.parent.data or None

    def apply_model(self, model):
        self.title.data = model.title
        self.active.data = model.active
        self.parent.data = str(model.parent_id or '')
