from onegov.form import Form
from onegov.translator_directory import _
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.models.language import Language
from wtforms.fields import StringField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError


class LanguageForm(Form):

    name = StringField(
        label=_('Name'),
        filters=[lambda s: s.strip() if isinstance(s, str) else s],
        validators=[DataRequired()]
    )

    def validate_name(self, field: StringField) -> None:
        query = self.request.session.query(Language)
        lang = query.filter_by(name=field.data).first()
        if isinstance(self.model, LanguageCollection) and lang:
            raise ValidationError(
                _('${language} already exists',
                  mapping={'language': field.data})
            )
        elif lang and not lang.id == self.model.id:
            raise ValidationError(
                _('${language} already exists',
                  mapping={'language': field.data})
            )
