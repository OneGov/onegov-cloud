from __future__ import annotations

from wtforms.fields import BooleanField

from onegov.form import Form
from onegov.form.fields import UploadMultipleField
from onegov.pas import _


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
