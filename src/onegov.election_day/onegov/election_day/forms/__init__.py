from onegov.election_day.forms.common import EmptyForm
from onegov.election_day.forms.data_source import DataSourceForm
from onegov.election_day.forms.data_source import DataSourceItemForm
from onegov.election_day.forms.election import ElectionForm
from onegov.election_day.forms.election_compound import ElectionCompoundForm
from onegov.election_day.forms.notification import TriggerNotificationForm
from onegov.election_day.forms.subscription import EmailSubscriptionForm
from onegov.election_day.forms.subscription import SmsSubscriptionForm
from onegov.election_day.forms.upload import UploadMajorzElectionForm
from onegov.election_day.forms.upload import UploadPartyResultsForm
from onegov.election_day.forms.upload import UploadProporzElectionForm
from onegov.election_day.forms.upload import UploadRestForm
from onegov.election_day.forms.upload import UploadVoteForm
from onegov.election_day.forms.upload import UploadWabstiMajorzElectionForm
from onegov.election_day.forms.upload import UploadWabstiProporzElectionForm
from onegov.election_day.forms.upload import UploadWabstiVoteForm
from onegov.election_day.forms.vote import VoteForm


__all__ = [
    'DataSourceForm',
    'DataSourceItemForm',
    'ElectionCompoundForm',
    'ElectionForm',
    'EmailSubscriptionForm',
    'EmptyForm',
    'EmptyForm',
    'SmsSubscriptionForm',
    'TriggerNotificationForm',
    'UploadMajorzElectionForm',
    'UploadPartyResultsForm',
    'UploadProporzElectionForm',
    'UploadRestForm',
    'UploadVoteForm',
    'UploadWabstiMajorzElectionForm',
    'UploadWabstiProporzElectionForm',
    'UploadWabstiVoteForm',
    'VoteForm',
]
