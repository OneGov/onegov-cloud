from __future__ import annotations

from onegov.core.crypto import random_token
from onegov.file.utils import as_fileintent
from onegov.form import Form
from onegov.form.fields import UploadField
from onegov.form.validators import FileSizeLimit
from onegov.form.validators import WhitelistedMimeType
from onegov.swissvotes import _
from onegov.swissvotes.models import SwissVoteFile


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.swissvotes.models import SwissVote


CSV_MIME_TYPES = {
    'text/csv',
    'text/plain'
}

XLSX_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/vnd.ms-office',
    'application/octet-stream',
    'application/zip'
}

PDF_MIME_TYPES = {
    'application/pdf'
}

SAV_MIME_TYPES = {
    'application/octet-stream',
}


DTA_MIME_TYPES = {
    'application/octet-stream',
}


class AttachmentsForm(Form):

    callout = _(
        'Uploading attachments may take some time due to full-text indexing.'
    )

    brief_description = UploadField(
        label=_('Brief description Swissvotes'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('General'),
    )

    voting_text = UploadField(
        label=_('Voting text'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('General'),
    )

    preliminary_examination = UploadField(
        label=_('Preliminary examination'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Submission'),
    )

    realization = UploadField(
        label=_('Realization'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Submission'),
    )

    federal_council_message = UploadField(
        label=_('Federal council message'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Pre-parliamentary phase'),
    )

    parliamentary_initiative = UploadField(
        label=_('Parliamentary initiative'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Parliamentary phase'),
    )

    parliamentary_committee_report = UploadField(
        label=_('Report of the parliamentary committee (only for Pa.Iv.)'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Parliamentary phase'),
    )

    federal_council_opinion = UploadField(
        label=_('Opinion of the Federal Council (only for Pa.Iv.)'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Parliamentary phase'),
    )

    parliamentary_debate = UploadField(
        label=_('Parliamentary debate'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Parliamentary phase'),
    )

    voting_booklet = UploadField(
        label=_('Voting booklet'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Voting campaign'),
    )

    easyvote_booklet = UploadField(
        label=_('Explanatory brochure by easyvote'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Voting campaign'),
    )

    ad_analysis = UploadField(
        label=_('Advertisment analysis'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Voting campaign'),
    )

    foeg_analysis = UploadField(
        label=_('Fög Analysis'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Voting campaign'),
    )

    campaign_finances_xlsx = UploadField(
        label=_('Campaign finances'),
        validators=[
            WhitelistedMimeType(XLSX_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Voting campaign'),
    )

    resolution = UploadField(
        label=_('Resolution'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Vote'),
    )

    results_by_domain = UploadField(
        label=_('Result by canton, district and municipality'),
        validators=[
            WhitelistedMimeType(XLSX_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Vote'),
    )

    post_vote_poll = UploadField(
        label=_('Full analysis of VOX post-vote poll results'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Post-vote polls'),
    )

    post_vote_poll_methodology = UploadField(
        label=_('Questionnaire of the VOX poll'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Post-vote polls'),
    )

    post_vote_poll_dataset = UploadField(
        label=_('Dataset of the VOX poll (CSV)'),
        validators=[
            WhitelistedMimeType(CSV_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Post-vote polls'),
    )

    post_vote_poll_dataset_sav = UploadField(
        label=_('Dataset of the VOX poll (SAV)'),
        validators=[
            WhitelistedMimeType(SAV_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Post-vote polls'),
    )

    post_vote_poll_dataset_dta = UploadField(
        label=_('Dataset of the VOX poll (DTA)'),
        validators=[
            WhitelistedMimeType(DTA_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Post-vote polls'),
    )

    post_vote_poll_codebook = UploadField(
        label=_('Codebook for the post-vote poll (PDF)'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Post-vote polls'),
    )

    post_vote_poll_codebook_xlsx = UploadField(
        label=_('Codebook for the post-vote poll (XLSX)'),
        validators=[
            WhitelistedMimeType(XLSX_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Post-vote polls'),
    )

    post_vote_poll_report = UploadField(
        label=_('Technical report on the VOX poll'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Post-vote polls'),
    )

    leewas_post_vote_poll_results = UploadField(
        label=_('Results of the LeeWas post-vote poll'),
        validators=[
            WhitelistedMimeType(PDF_MIME_TYPES),
            FileSizeLimit(120 * 1024 * 1024)
        ],
        fieldset=_('Post-vote polls'),
    )

    def update_model(self, model: SwissVote) -> None:
        locale = self.request.locale

        for field in self:
            name = field.name
            action = getattr(field, 'action', '')

            if action == 'delete':
                delattr(model, name)
            elif action == 'replace' and field.data:
                assert isinstance(field, UploadField)
                assert field.file is not None
                file = SwissVoteFile(id=random_token())
                file.reference = as_fileintent(
                    field.file,
                    f'{name}-{locale}'
                )
                setattr(model, name, file)

    def apply_model(self, model: SwissVote) -> None:
        file: SwissVoteFile | None
        for field in self:
            name = field.name
            file = getattr(model, name, None)
            if file:
                field.data = {
                    'filename': file.reference.filename,
                    'size': file.reference.file.content_length,
                    'mimetype': file.reference.content_type
                }
