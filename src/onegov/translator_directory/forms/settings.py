from __future__ import annotations

from onegov.form import Form
from onegov.gis import CoordinatesField
from onegov.translator_directory import _
from onegov.user import User
from sqlalchemy import func
from wtforms.fields import EmailField
from wtforms.fields import URLField
from wtforms.validators import Email
from wtforms.validators import Optional
from wtforms.validators import URL
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.translator_directory.app import TranslatorDirectoryApp


ALLOWED_MIME_TYPES = {
    'application/excel',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-office',
}


class TranslatorDirectorySettingsForm(Form):

    coordinates = CoordinatesField(
        fieldset=_('Home Location'),
        render_kw={'data-map-type': 'marker', 'data-undraggable': 1},
    )

    declaration_link = URLField(
        label=_('Link to declaration of authorization'),
        fieldset=_('Accreditation'),
        validators=[URL(), Optional()]
    )

    def validate_accountant_email(self, field: EmailField) -> None:
        if field.data:
            field.data = field.data.lower()
            user_exists = self.request.session.query(
                self.request.session.query(User)
                .filter(func.lower(User.username) == field.data)
                .exists()
            ).scalar()
            if not user_exists:
                raise ValidationError(
                    _(
                        'No user with this email address exists. '
                        'Please create a user account first.'
                    )
                )

    def update_model(self, app: TranslatorDirectoryApp) -> None:
        app.org.meta = app.org.meta or {}
        if self.coordinates.data:
            app.coordinates = self.coordinates.data
        app.org.meta['declaration_link'] = self.declaration_link.data

    def apply_model(self, app: TranslatorDirectoryApp) -> None:
        self.coordinates.data = app.coordinates
        self.declaration_link.data = app.org.meta.get('declaration_link', '')
