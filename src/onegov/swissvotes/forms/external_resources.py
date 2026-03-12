from __future__ import annotations

from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.swissvotes import _
from wtforms.validators import InputRequired
from wtforms.validators import ValidationError


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.swissvotes.request import SwissvotesRequest


class UpdateExternalResourcesForm(Form):

    request: SwissvotesRequest

    callout = _('Updating the external resources may take some time.')

    resources = MultiCheckboxField(
        label=_('Resource'),
        choices=(
            ('mfg', _('eMuseum.ch')),
            ('bs', _('Plakatsammlung Basel')),
            ('sa', _('Social Archives')),
        ),
        default=('mfg', 'bs', 'sa'),
        validators=[
            InputRequired()
        ],
    )

    def validate_resources(self, field: MultiCheckboxField) -> None:
        assert self.resources.data is not None
        if 'mfg' in self.resources.data and not self.request.app.mfg_api_token:
            raise ValidationError(_('No eMuseum API key available.'))
        if 'bs' in self.resources.data and not self.request.app.bs_api_token:
            raise ValidationError(_('No Plakatsammlung API key available.'))
