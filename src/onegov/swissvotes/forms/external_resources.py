from onegov.form import Form
from onegov.form.fields import MultiCheckboxField
from onegov.swissvotes import _
from wtforms import ValidationError
from wtforms.validators import InputRequired


class UpdateExternalResourcesForm(Form):

    callout = _('Updating the external resources may take some time.')

    resources = MultiCheckboxField(
        label=_('Resource'),
        choices=(
            ('mfg', _('eMuseum.ch')),
            ('sa', _('Social Archives')),
        ),
        default=('mfg', 'sa'),
        validators=[
            InputRequired()
        ],
    )

    def validate_resources(self, field):
        if 'mfg' in self.resources.data and not self.request.app.mfg_api_token:
            raise ValidationError(_('No eMuseum API key available.'))
