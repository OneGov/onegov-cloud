from onegov.election_day.forms.data_source import DataSourceForm
from onegov.election_day.forms.data_source import DataSourceItemForm
from onegov.election_day.forms.election import ElectionForm
from onegov.election_day.forms.subscribe import SubscribeForm
from onegov.election_day.forms.upload import UploadElectionPartyResultsForm
from onegov.election_day.forms.upload import UploadMajorzElectionForm
from onegov.election_day.forms.upload import UploadProporzElectionForm
from onegov.election_day.forms.upload import UploadVoteForm
from onegov.election_day.forms.upload import UploadWabstiMajorzElectionForm
from onegov.election_day.forms.upload import UploadWabstiProporzElectionForm
from onegov.election_day.forms.upload import UploadWabstiVoteForm
from onegov.election_day.forms.vote import VoteForm
from onegov.form import Form


class DeleteForm(Form):
    pass


class TriggerNotificationForm(Form):
    pass


__all__ = [
    'DataSourceForm',
    'DataSourceItemForm',
    'DeleteForm',
    'ElectionForm',
    'SubscribeForm',
    'TriggerNotificationForm',
    'UploadElectionPartyResultsForm',
    'UploadMajorzElectionForm',
    'UploadProporzElectionForm',
    'UploadVoteForm',
    'UploadWabstiMajorzElectionForm',
    'UploadWabstiProporzElectionForm',
    'UploadWabstiVoteForm',
    'VoteForm',
]
