from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.swissvotes import _
from onegov.swissvotes.models import SwissVoteFile


XLSX_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-office',
    'application/octet-stream',
    'application/zip'
}


class AttachmentsForm(Form):

    callout = _(
        "Uploading attachments may take some time due to full-text indexing."
    )

    voting_text = UploadField(
        label=_("Voting text"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    brief_description = UploadField(
        label=_("Brief description Swissvotes"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    federal_council_message = UploadField(
        label=_("Federal council message"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    parliamentary_debate = UploadField(
        label=_("Parliamentary debate"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    voting_booklet = UploadField(
        label=_("Voting booklet"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    resolution = UploadField(
        label=_("Resolution"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    realization = UploadField(
        label=_("Realization"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    ad_analysis = UploadField(
        label=_("Advertisment analysis"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    results_by_domain = UploadField(
        label=_("Result by canton, district and municipality"),
        validators=[
            WhitelistedMimeType(XLSX_MIME_TYPES),
            FileSizeLimit(50 * 1024 * 1024)
        ]
    )

    def update_model(self, model):
        locale = self.request.locale

        for field in self:
            name = field.name
            action = getattr(field, 'action', '')
            if action == 'delete':
                delattr(model, name)
            if action == 'replace':
                if field.data:
                    file = SwissVoteFile(id=random_token())
                    file.reference = as_fileintent(
                        field.raw_data[-1].file,
                        f'{name}-{locale}'
                    )
                    setattr(model, name, file)

    def apply_model(self, model):
        for field in self:
            name = field.name
            file = getattr(model, name, None)
            if file:
                field.data = {
                    'filename': file.reference.filename,
                    'size': file.reference.file.content_length,
                    'mimetype': file.reference.content_type
                }
