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

    def update_model(self, model):
        locale = self.request.locale
        if self.voting_text.action == 'delete':
            del model.voting_text
        if self.voting_text.action == 'replace':
            if self.voting_text.data:
                voting_text = SwissVoteFile(id=random_token())
                voting_text.reference = as_fileintent(
                    self.voting_text.raw_data[-1].file,
                    f'voting_text-{locale}'
                )
                model.voting_text = voting_text

        if self.federal_council_message.action == 'delete':
            del model.federal_council_message
        if self.federal_council_message.action == 'replace':
            if self.federal_council_message.data:
                federal_council_message = SwissVoteFile(id=random_token())
                federal_council_message.reference = as_fileintent(
                    self.federal_council_message.raw_data[-1].file,
                    f'federal_council_message-{locale}'
                )
                model.federal_council_message = federal_council_message

        if self.parliamentary_debate.action == 'delete':
            del model.parliamentary_debate
        if self.parliamentary_debate.action == 'replace':
            if self.parliamentary_debate.data:
                parliamentary_debate = SwissVoteFile(id=random_token())
                parliamentary_debate.reference = as_fileintent(
                    self.parliamentary_debate.raw_data[-1].file,
                    f'parliamentary_debate-{locale}'
                )
                model.parliamentary_debate = parliamentary_debate

    def apply_model(self, model):
        def assign_file(field, file):
            # todo: implement something better
            fs = FieldStorage()
            fs.file = BytesIO(file.reference.file.read())
            fs.type = file.reference.content_type
            fs.filename = file.reference.filename
            field.data = field.process_fieldstorage(fs)

        if self.model.voting_text:
            assign_file(
                self.voting_text,
                self.model.voting_text
            )
        if self.model.federal_council_message:
            assign_file(
                self.federal_council_message,
                self.model.federal_council_message
            )
        if self.model.parliamentary_debate:
            assign_file(
                self.parliamentary_debate,
                self.model.parliamentary_debate
            )
