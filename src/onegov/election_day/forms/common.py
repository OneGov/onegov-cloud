from onegov.election_day import _
from onegov.form import Form
from wtforms import StringField
from wtforms import ValidationError
from wtforms.validators import InputRequired


class EmptyForm(Form):
    pass


class ChangeIdForm(Form):

    callout = _(
        "The ID is used in the URL and might be used somewhere. Changing the"
        "ID might break links on external sites!"
    )

    id = StringField(
        label=_("ID"),
        validators=[
            InputRequired()
        ],
    )

    def validate_id(self, field):
        if self.model.id != field.data:
            query = self.request.session.query(self.model.__class__.id)
            query = query.filter_by(id=field.data)
            if query.first():
                raise ValidationError(_('ID already exists'))

    def update_model(self, model):
        model.id = self.id.data

    def apply_model(self, model):
        self.id.data = model.id
