from itertools import chain
from onegov.ballot import BallotResult
from onegov.ballot import Vote
from onegov.election_day import _
from onegov.election_day.formats.common import EXPATS
from onegov.election_day.formats.common import FileImportError
from onegov.election_day.formats.common import get_entity_and_district
from onegov.election_day.formats.common import load_xml
from sqlalchemy import or_
from uuid import uuid4
from xsdata_ech.e_ch_0252_1_0 import VoterTypeType
from xsdata_ech.e_ch_0252_1_0 import VoteSubTypeType


def import_xml(principal, session, file, vote=None):
    """ Tries to import the given eCH-0252 XML file.

    This is the format used by onegov.ballot.Vote.export_xml.

    This function is typically called automatically every few minutes during
    an election day - we use bulk inserts to speed up the import.

    :return:
        A list containing errors.

    """

    delivery, error = load_xml(file)
    if error:
        return [error]

    results = []
    for vote_info in delivery.vote_base_delivery.vote_info:
        results.append(
            import_vote_xml(principal, session, vote_info, vote=vote)
        )

    items, errors = zip(*results)
    errors = list(chain.from_iterable(errors))
    if vote and not items and not errors:
        errors.append(FileImportError(_('No data found')))

    return errors, set(items)


def import_vote_xml(principal, session, vote_info, vote=None):
    """ Imports a vote_info from a delivery, optionally to a give vote. """

    # get vote
    identification = (
        vote_info.vote.main_vote_identification
        or vote_info.vote.vote_identification
    )
    if not vote:
        vote = session.query(Vote).filter(
            or_(
                Vote.id == identification,
                Vote.external_id == identification
            )
        ).first()
    if not vote or identification not in (vote.id, vote.external_id):
        return None, []

    # get ballot
    ballot = None
    if vote_info.vote.vote_sub_type == VoteSubTypeType.VALUE_1:
        ballot = vote.proposal
    elif vote_info.vote.vote_sub_type == VoteSubTypeType.VALUE_2:
        if vote.type == 'complex':
            ballot = vote.counter_proposal
    elif vote_info.vote.vote_sub_type == VoteSubTypeType.VALUE_3:
        if vote.type == 'complex':
            ballot = vote.tie_breaker
    if not ballot:
        return vote, [
            FileImportError(
                _('Vote type not supported'),
                filename=identification,
            )
        ]

    # get entities
    results = {}
    errors = []
    entities = principal.entities[vote.date.year]
    status = 'final'
    for circle_info in vote_info.counting_circle_info:
        result = circle_info.result_data
        voters = result.count_of_voters_information
        try:
            entity_id = int(circle_info.counting_circle.counting_circle_id)
            assert entity_id is not None
            entity_id = 0 if entity_id in EXPATS else entity_id
            assert entity_id == 0 or entity_id in entities

            line_errors = []
            name, district, superregion = get_entity_and_district(
                entity_id, entities, vote, principal, line_errors
            )
            assert not line_errors

            expats = [
                subtotal.count_of_voters for subtotal in voters.subtotal_info
                if subtotal.voter_type == VoterTypeType.VALUE_2
            ]
            expats = expats[0] if expats else None
            assert expats is None or isinstance(expats, int)

            if not result.fully_counted_true:
                status = 'interim'

            result = {
                'id': uuid4(),
                'ballot_id': ballot.id,
                'entity_id': entity_id,
                'name': name,
                'district': district,
                'eligible_voters': voters.count_of_voters_total,
                'expats': expats,
                'counted': result.fully_counted_true,
                'invalid': result.received_invalid_votes or 0,
                'empty': result.received_blank_votes or 0,
                'yeas': result.count_of_yes_votes or 0,
                'nays': result.count_of_no_votes or 0,
            }
        except (AssertionError, TypeError, ValueError):
            errors.append(
                FileImportError(
                    _('Invalid values'),
                    filename=identification,
                    line=circle_info.counting_circle.counting_circle_id
                ),
            )
        else:
            results[entity_id] = result

    if not errors:
        ballot.clear_results()
        vote.last_result_change = vote.timestamp()
        vote.status = status
        session.bulk_insert_mappings(BallotResult, results.values())

    return vote, errors
