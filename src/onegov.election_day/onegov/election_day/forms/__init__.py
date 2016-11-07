from onegov.election_day.forms.election import ElectionForm
from onegov.election_day.forms.subscribe import SubscribeForm
from onegov.election_day.forms.upload import UploadElectionForm
from onegov.election_day.forms.upload import UploadVoteForm
from onegov.election_day.forms.vote import VoteForm
from onegov.form import Form


class DeleteForm(Form):
    pass


class TriggerNotificationForm(Form):
    pass


__all__ = [
    'DeleteForm',
    'ElectionForm',
    'SubscribeForm',
    'TriggerNotificationForm',
    'UploadElectionForm',
    'UploadVoteForm',
    'VoteForm'
]
