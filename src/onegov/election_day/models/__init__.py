from __future__ import annotations

from onegov.election_day.models.archived_result import ArchivedResult
from onegov.election_day.models.data_source import DataSource
from onegov.election_day.models.data_source import DataSourceItem
from onegov.election_day.models.election import Candidate
from onegov.election_day.models.election import CandidatePanachageResult
from onegov.election_day.models.election import CandidateResult
from onegov.election_day.models.election import Election
from onegov.election_day.models.election import ElectionRelationship
from onegov.election_day.models.election import ElectionResult
from onegov.election_day.models.election import List
from onegov.election_day.models.election import ListConnection
from onegov.election_day.models.election import ListPanachageResult
from onegov.election_day.models.election import ListResult
from onegov.election_day.models.election import ProporzElection
from onegov.election_day.models.election_compound import ElectionCompound
from onegov.election_day.models.election_compound import ElectionCompoundPart
from onegov.election_day.models.election_compound import \
    ElectionCompoundRelationship
from onegov.election_day.models.notification import EmailNotification
from onegov.election_day.models.notification import Notification
from onegov.election_day.models.notification import SmsNotification
from onegov.election_day.models.notification import WebhookNotification
from onegov.election_day.models.party_result import PartyPanachageResult
from onegov.election_day.models.party_result import PartyResult
from onegov.election_day.models.principal import Canton
from onegov.election_day.models.principal import Municipality
from onegov.election_day.models.principal import Principal
from onegov.election_day.models.screen import Screen
from onegov.election_day.models.subscriber import EmailSubscriber
from onegov.election_day.models.subscriber import SmsSubscriber
from onegov.election_day.models.subscriber import Subscriber
from onegov.election_day.models.upload_token import UploadToken
from onegov.election_day.models.vote import Ballot
from onegov.election_day.models.vote import BallotResult
from onegov.election_day.models.vote import ComplexVote
from onegov.election_day.models.vote import Vote


__all__ = [
    'ArchivedResult',
    'Ballot',
    'BallotResult',
    'Candidate',
    'CandidatePanachageResult',
    'CandidateResult',
    'Canton',
    'ComplexVote',
    'DataSource',
    'DataSourceItem',
    'Election',
    'ElectionCompound',
    'ElectionCompoundPart',
    'ElectionCompoundRelationship',
    'ElectionRelationship',
    'ElectionResult',
    'EmailNotification',
    'EmailSubscriber',
    'List',
    'ListConnection',
    'ListPanachageResult',
    'ListResult',
    'Municipality',
    'Notification',
    'PartyPanachageResult',
    'PartyResult',
    'Principal',
    'ProporzElection',
    'Screen',
    'SmsNotification',
    'SmsSubscriber',
    'Subscriber',
    'UploadToken',
    'Vote',
    'WebhookNotification',
]
