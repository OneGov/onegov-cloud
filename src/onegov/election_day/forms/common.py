from onegov.core.utils import normalize_for_url
from onegov.election_day import _
from onegov.form import Form
from wtforms.fields import StringField
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


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
        if normalize_for_url(field.data) != field.data:
            raise ValidationError(_('Invalid ID'))
        if self.model.id != field.data:
            query = self.request.session.query(self.model.__class__.id)
            query = query.filter_by(id=field.data)
            if query.first():
                raise ValidationError(_('ID already exists'))

    def update_model(self, model):
        model.id = self.id.data

    def apply_model(self, model):
        self.id.data = model.id
