from __future__ import annotations

from onegov.election_day.forms.upload.election_compound import (
    UploadElectionCompoundForm)
from onegov.election_day.forms.upload.election import UploadMajorzElectionForm
from onegov.election_day.forms.upload.election import UploadProporzElectionForm
from onegov.election_day.forms.upload.party_results import (
    UploadPartyResultsForm)
from onegov.election_day.forms.upload.rest import UploadRestForm
from onegov.election_day.forms.upload.vote import UploadVoteForm
from onegov.election_day.forms.upload.wabsti_majorz import (
    UploadWabstiMajorzElectionForm)
from onegov.election_day.forms.upload.wabsti_proporz import (
    UploadWabstiProporzElectionForm)
from onegov.election_day.forms.upload.wabsti_vote import UploadWabstiVoteForm


__all__ = (
    'UploadElectionCompoundForm',
    'UploadMajorzElectionForm',
    'UploadPartyResultsForm',
    'UploadProporzElectionForm',
    'UploadRestForm',
    'UploadVoteForm',
    'UploadWabstiMajorzElectionForm',
    'UploadWabstiProporzElectionForm',
    'UploadWabstiVoteForm',
)
