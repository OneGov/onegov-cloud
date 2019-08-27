from onegov.form import Form
from onegov.form.fields import ChosenSelectField
from onegov.form.validators import UniqueColumnValue
from onegov.gazette import _
from onegov.gazette.models import GazetteNotice
from onegov.gazette.models import Organization
from onegov.gazette.validators import UnusedColumnKeyValue
from sqlalchemy import cast
from sqlalchemy import String
from wtforms import BooleanField
from wtforms import StringField
from wtforms.validators import InputRequired


class OrganizationForm(Form):

    parent = ChosenSelectField(
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

    name = StringField(
        label=_("ID"),
        description=_("Leave blank to set the value automatically."),
        validators=[
            UniqueColumnValue(Organization),
            UnusedColumnKeyValue(GazetteNotice._organizations)
        ]
    )

    external_name = StringField(
        label=_("External ID"),
    )

    def on_request(self):
        session = self.request.session
        query = session.query(
            cast(Organization.id, String),
            Organization.title
        )
        query = query.filter(Organization.parent_id.is_(None))
        query = query.order_by(Organization.order)
        self.parent.choices = query.all()
        self.parent.choices.insert(
            0, ('', self.request.translate(_("- none -")))
        )

    def update_model(self, model):
        model.title = self.title.data
        model.active = self.active.data
        model.parent_id = self.parent.data or None
        if self.name.data:
            model.name = self.name.data
        model.external_name = self.external_name.data

    def apply_model(self, model):
        self.title.data = model.title
        self.active.data = model.active
        self.name.data = model.name
        self.external_name.data = model.external_name
        self.parent.data = str(model.parent_id or '')
        if model.in_use:
            self.name.render_kw = {'readonly': True}
