from onegov.election_day import _
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES
from onegov.election_day.forms.upload.common import ALLOWED_MIME_TYPES_XML
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
    from onegov.ballot.models import Vote
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality


class UploadVoteForm(Form):

    file_format = RadioField(
        _("File format"),
        choices=[
            ('internal', "OneGov Cloud"),
            ('xml', "eCH-0252"),
        ],
        validators=[
            InputRequired()
        ],
        default='internal'
    )

    xml = UploadField(
        label=_("Delivery"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES_XML),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'xml'),
        render_kw={'force_simple': True}
    )

    proposal = UploadField(
        label=_("Proposal / Results"),
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', '!wabsti_c', 'file_format', '!xml'),
        render_kw={'force_simple': True}
    )

    sg_gemeinden = UploadField(
        label="SG_Gemeinden.csv",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw={'force_simple': True}
    )

    sg_geschaefte = UploadField(
        label="SG_Geschaefte.csv",
        validators=[
            DataRequired(),
            WhitelistedMimeType(ALLOWED_MIME_TYPES),
            FileSizeLimit(MAX_FILE_SIZE)
        ],
        depends_on=('file_format', 'wabsti_c'),
        render_kw={'force_simple': True}
    )

    def adjust(self, principal: 'Canton | Municipality', vote: 'Vote') -> None:
        """ Adjusts the form to the given principal and vote. """

        assert hasattr(vote, 'data_sources')
        if vote.data_sources:
            self.file_format.choices = [
                ('internal', "OneGov Cloud"),
                ('xml', "eCH-0252"),
                ('wabsti_c', "WabstiCExport")
            ]
