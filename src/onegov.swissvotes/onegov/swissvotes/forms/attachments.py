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

        if self.voting_booklet.action == 'delete':
            del model.voting_booklet
        if self.voting_booklet.action == 'replace':
            if self.voting_booklet.data:
                voting_booklet = SwissVoteFile(id=random_token())
                voting_booklet.reference = as_fileintent(
                    self.voting_booklet.raw_data[-1].file,
                    f'voting_booklet-{locale}'
                )
                model.voting_booklet = voting_booklet

        if self.resolution.action == 'delete':
            del model.resolution
        if self.resolution.action == 'replace':
            if self.resolution.data:
                resolution = SwissVoteFile(id=random_token())
                resolution.reference = as_fileintent(
                    self.resolution.raw_data[-1].file,
                    f'resolution-{locale}'
                )
                model.resolution = resolution

        if self.realization.action == 'delete':
            del model.realization
        if self.realization.action == 'replace':
            if self.realization.data:
                realization = SwissVoteFile(id=random_token())
                realization.reference = as_fileintent(
                    self.realization.raw_data[-1].file,
                    f'realization-{locale}'
                )
                model.realization = realization

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
        if self.model.voting_booklet:
            assign_file(
                self.voting_booklet,
                self.model.voting_booklet
            )
        if self.model.resolution:
            assign_file(
                self.resolution,
                self.model.resolution
            )
        if self.model.realization:
            assign_file(
                self.realization,
                self.model.realization
            )
