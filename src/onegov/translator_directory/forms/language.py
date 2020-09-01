from wtforms import StringField, ValidationError
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.translator_directory import _


class LanguageForm(Form):

    name = StringField(
        label=_('Name'),
        validators=[InputRequired()]
    )

    def validate_name(self, field):
        # just to be very sure nobody enters empty values
        if not field.data.strip():
            raise ValidationError(
                _('This field is required.')
            )

        # We correct user input here
        field.data = field.data.strip().lower().capitalize()

        query = self.request.session.query(self.model.model_class)

        if query.filter_by(name=field.data).first():
            raise ValidationError(
                _("${language} already exists",
                  mapping={'language': field.data})
            )
