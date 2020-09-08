from wtforms import StringField, ValidationError
from wtforms.validators import InputRequired

from onegov.form import Form
from onegov.translator_directory import _
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.models.translator import Language


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

        query = self.request.session.query(Language)
        lang = query.filter_by(name=field.data).first()
        if isinstance(self.model, LanguageCollection) and lang:
            raise ValidationError(
                _("${language} already exists",
                  mapping={'language': field.data})
            )
        elif lang and not lang.id == self.model.id:
            raise ValidationError(
                _("${language} already exists",
                  mapping={'language': field.data})
            )
