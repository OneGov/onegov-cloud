from __future__ import annotations

from onegov.election_day.collections.archived_results import \
    ArchivedResultCollection
from onegov.election_day.collections.archived_results import \
    SearchableArchivedResultCollection
from onegov.election_day.collections.ballots import BallotCollection
from onegov.election_day.collections.candidates import CandidateCollection
from onegov.election_day.collections.data_sources import DataSourceCollection
from onegov.election_day.collections.data_sources import \
    DataSourceItemCollection
from onegov.election_day.collections.election_compounds import \
    ElectionCompoundCollection
from onegov.election_day.collections.elections import ElectionCollection
from onegov.election_day.collections.lists import ListCollection
from onegov.election_day.collections.notifications import \
    NotificationCollection
from onegov.election_day.collections.screens import ScreenCollection
from onegov.election_day.collections.subscribers import \
    EmailSubscriberCollection
from onegov.election_day.collections.subscribers import SmsSubscriberCollection
from onegov.election_day.collections.subscribers import SubscriberCollection
from onegov.election_day.collections.upload_tokens import UploadTokenCollection
from onegov.election_day.collections.votes import VoteCollection


__all__ = [
    'ArchivedResultCollection',
    'BallotCollection',
    'CandidateCollection',
    'DataSourceCollection',
    'DataSourceItemCollection',
    'ElectionCollection',
    'ElectionCompoundCollection',
    'EmailSubscriberCollection',
    'ListCollection',
    'NotificationCollection',
    'ScreenCollection',
    'SearchableArchivedResultCollection',
    'SmsSubscriberCollection',
    'SubscriberCollection',
    'UploadTokenCollection',
    'VoteCollection',
]
