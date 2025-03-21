from __future__ import annotations

from onegov.form import Form
from onegov.pas import _
from wtforms.fields import BooleanField
from onegov.form.fields import UploadMultipleField


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass


class DataImportForm(Form):
    clean = BooleanField(label=_('Delete data before import'), default=False)

    people_source = UploadMultipleField(
        label=_('People Data (JSON)'),
        description=_('JSON file containing parliamentarian data.'),
    )
    organizations_source = UploadMultipleField(
        label=_('Organizations Data (JSON)'),
        description=_(
            'JSON file containing organization data (commissions, '
            'parties, etc.).'
        ),
    )
    memberships_source = UploadMultipleField(
        label=_('Memberships Data (JSON)'),
        description=_(
            'JSON file containing membership data (who is member of '
            'what organization).'
        ),
    )

    # def validate_people_source(self, field):
    #     return True
    #     if field.data:
    #         try:
    #             _load_json(field.data)
    #         except JSONDecodeError:
    #             raise ValidationError(_('Invalid JSON file.'))
    #
    # def validate_organizations_source(self, field):
    #     return True
    #     if field.data:
    #         try:
    #             _load_json(field.data)
    #         except JSONDecodeError:
    #             raise ValidationError(_('Invalid JSON file.'))
    #
    # def validate_memberships_source(self, field):
    #     return True
    #     if field.data:
    #         try:
    #             _load_json(field.data)
    #         except JSONDecodeError:
    #             raise ValidationError(_('Invalid JSON file.'))
