from __future__ import annotations

from onegov.form.fields import UploadField
from json import JSONDecodeError

from onegov.pas import _
from onegov.pas.importer.json_import import import_zug_kub_data, _load_json
from onegov.pas.layouts import (
    DefaultLayout,
)
from onegov.form import Form

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from onegov.town6.request import TownRequest
    from webob import Response
    from wtforms.validators import DataRequired, ValidationError


from wtforms.validators import DataRequired


class DataImportForm(Form):

    people_source = UploadField(
        label=_('People Data (JSON)'),
        validators=[DataRequired()],
        description=_("JSON file containing parliamentarian data."),
    )
    organizations_source = UploadField(
        label=_('Organizations Data (JSON)'),
        validators=[DataRequired()],
        description=_(
            "JSON file containing organization data (commissions, "
            "parties, etc.)."
        ),
    )
    memberships_source = UploadField(
        label=_('Memberships Data (JSON)'),
        validators=[DataRequired()],
        description=_(
            "JSON file containing membership data (who is member of "
            "what organization)."
        ),
    )

    def validate_people_source(self, field):
        if field.data:
            try:
                _load_json(field.data)
            except JSONDecodeError:
                raise ValidationError(_('Invalid JSON file.'))

    def validate_organizations_source(self, field):
        if field.data:
            try:
                _load_json(field.data)
            except JSONDecodeError:
                raise ValidationError(_('Invalid JSON file.'))

    def validate_memberships_source(self, field):
        if field.data:
            try:
                _load_json(field.data)
            except JSONDecodeError:
                raise ValidationError(_('Invalid JSON file.'))
