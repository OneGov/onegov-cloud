from onegov.election_day.forms.election import ElectionForm
from onegov.election_day.forms.upload import (
    UploadElectionForm,
    UploadVoteForm
)
from onegov.election_day.forms.vote import VoteForm
from onegov.form import Form


class DeleteForm(Form):
    pass


class TriggerWebhookForm(Form):
    pass


__all__ = [
    'DeleteForm',
    'ElectionForm',
    'UploadElectionForm',
    'UploadVoteForm',
    'VoteForm'
]
