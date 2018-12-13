from cgi import FieldStorage
from io import BytesIO
from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.swissvotes import _
from onegov.swissvotes.models import SwissVoteFile


class AttachmentsForm(Form):

    voting_text = UploadField(
        label=_("Voting text"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(25 * 1024 * 1024)
        ]
    )

    federal_council_message = UploadField(
        label=_("Federal council message"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(25 * 1024 * 1024)
        ]
    )

    parliamentary_debate = UploadField(
        label=_("Parliamentary debate"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(25 * 1024 * 1024)
        ]
    )

    voting_booklet = UploadField(
        label=_("Voting booklet"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(25 * 1024 * 1024)
        ]
    )

    resolution = UploadField(
        label=_("Resolution"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(25 * 1024 * 1024)
        ]
    )

    realization = UploadField(
        label=_("Realization"),
        validators=[
            WhitelistedMimeType({'application/pdf'}),
            FileSizeLimit(25 * 1024 * 1024)
        ]
    )

    def update_model(self, model):
        locale = self.request.locale

        for name in self._fields.keys():
            field = getattr(self, name)
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
        for name in self._fields.keys():
            field = getattr(self, name)
            file = getattr(model, name, None)
            if file:
                fs = FieldStorage()
                fs.file = BytesIO(file.reference.file.read())
                fs.type = file.reference.content_type
                fs.filename = file.reference.filename
                field.data = field.process_fieldstorage(fs)
