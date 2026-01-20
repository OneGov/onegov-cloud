from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import MAX_FILE_SIZE
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from wtforms.fields import RadioField
from wtforms.validators import DataRequired
from wtforms.validators import InputRequired


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from onegov.election_day.models import Vote


class UploadVoteForm(Form):

    file_format = RadioField(
        _('File format'),
        choices=[('internal', 'OneGov Cloud')],
        validators=[
            InputRequired()
        ],
        default='internal'
    )

    proposal = UploadField(
        label=_('Proposal / Results'),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', '!wabsti_c'),
        render_kw={'force_simple': True}
    )

    sg_gemeinden = UploadField(
        label='SG_Gemeinden.csv',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw={'force_simple': True}
    )

    sg_geschaefte = UploadField(
        label='SG_Geschaefte.csv',
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw={'force_simple': True}
    )

    def adjust(self, principal: Canton | Municipality, vote: Vote) -> None:
        """ Adjusts the form to the given principal and vote. """

        assert hasattr(vote, 'data_sources')
        if vote.data_sources:
            self.file_format.choices = [
                ('internal', 'OneGov Cloud'),
                ('wabsti_c', 'WabstiCExport')
            ]
