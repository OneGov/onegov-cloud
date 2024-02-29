from onegov.ballot import Ballot
from onegov.ballot import BallotResult
from onegov.ballot import ComplexVote
from onegov.ballot import Vote
from onegov.election_day import _
from onegov.election_day.formats.imports.common import convert_ech_domain
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from sqlalchemy.orm import joinedload
from xsdata_ech.e_ch_0252_1_0 import VoteInfoType
from xsdata_ech.e_ch_0252_1_0 import VoterTypeType
from xsdata_ech.e_ch_0252_1_0 import VoteSubTypeType

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot.types import Status
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from sqlalchemy.orm import Session
    from xsdata_ech.e_ch_0252_1_0 import EventVoteBaseDeliveryType as V1
    from xsdata_ech.e_ch_0252_2_0 import EventVoteBaseDeliveryType as V2


def import_votes_ech(
    principal: 'Canton | Municipality',
    vote_base_delivery: 'V1 | V2',
    session: 'Session'
) -> tuple[list[FileImportError], set[Vote], set[Vote]]:
    """ Imports all votes in a given eCH-0252 delivery.

    Deletes votes on the same day not appearing in the delivery.

    :return:
        A tuple consisting of a list with errors, a set with updated
        votes, and a set with deleted votes

    """

    assert vote_base_delivery.polling_day is not None
    polling_day = vote_base_delivery.polling_day.to_date()
    entities = principal.entities[polling_day.year]

    # extract vote and ballot structure
    classes: dict[str, type[Vote] | type[ComplexVote]] = {}
    for vote_info in vote_base_delivery.vote_info:
        assert vote_info.vote
        sub_type = vote_info.vote.vote_sub_type
        if sub_type == VoteSubTypeType.VALUE_1:
            classes.setdefault(vote_info.vote.vote_identification or '', Vote)
        elif sub_type in (VoteSubTypeType.VALUE_2, VoteSubTypeType.VALUE_3):
            classes[vote_info.vote.main_vote_identification or ''] = \
                ComplexVote

    # get or create votes
    existing_votes = session.query(Vote).filter(
        Vote.date == polling_day
    ).options(joinedload(Vote.ballots, Ballot.results)).all()
    votes = {}
    for identification, cls in classes.items():
        vote = None
        for existing in existing_votes:
            if identification in (existing.id, existing.external_id):
                vote = existing
                break
        if not vote:
            vote = cls(
                id=identification.lower(),
                external_id=identification,
                date=polling_day,
                domain='federation',
                title_translations={}
            )
            session.add(vote)
        if not isinstance(vote, cls):
            return [
                FileImportError(_(
                    'Vote types cannot be changed automatically, please '
                    'delete manually'
                ))
            ], set(), set()
        votes[identification] = vote

    # delete obsolete votes
    deleted = {vote for vote in existing_votes if vote not in votes.values()}

    # update information and add results
    errors = []
    for vote_info in vote_base_delivery.vote_info:
        assert vote_info.vote
        identification = (
            vote_info.vote.main_vote_identification
            or vote_info.vote.vote_identification
            or ''
        )
        title_translations = {
            f'{title.language.lower()}_CH': title.vote_title
            for title in vote_info.vote.vote_title_information
            if title.vote_title and title.language
        }
        vote = votes[identification]
        vote.last_result_change = vote.timestamp()
        ballot = vote.proposal
        if vote_info.vote.vote_sub_type == VoteSubTypeType.VALUE_1:
            assert vote_info.vote.domain_of_influence
            supported, domain, domain_segment = convert_ech_domain(
                vote_info.vote.domain_of_influence, principal, entities
            )
            if not supported:
                errors.append(
                    FileImportError(
                        _('Domain not supported'),
                        filename=identification
                    )
                )
                continue
            vote.domain = domain
            vote.domain_segment = domain_segment
            vote.title_translations = title_translations
            if vote_info.vote.sequence is not None:
                vote.shortcode = str(vote_info.vote.sequence)
        elif vote_info.vote.vote_sub_type == VoteSubTypeType.VALUE_2:
            assert isinstance(vote, ComplexVote)
            vote.counter_proposal.title_translations = title_translations
            ballot = vote.counter_proposal
        elif vote_info.vote.vote_sub_type == VoteSubTypeType.VALUE_3:
            assert isinstance(vote, ComplexVote)
            vote.tie_breaker.title_translations = title_translations
            ballot = vote.tie_breaker
        else:
            errors.append(
                FileImportError(
                    _('Vote type not supported'),
                    filename=identification
                )
            )
            continue

        _import_results(
            principal, entities, vote_info, identification, vote, ballot
        )

    return errors, set(votes.values()), deleted


def _import_results(
    principal: 'Canton | Municipality',
    entities: dict[int, dict[str, str]],
    vote_info: VoteInfoType,
    identification: str,
    vote: Vote,
    ballot: Ballot,
) -> tuple[Vote | None, list[FileImportError]]:

    """ Import results of a single ballot """

    assert vote_info.vote is not None

    results = {}
    errors = []
    status: 'Status' = 'final'
    entity_id_str = None
    for circle_info in vote_info.counting_circle_info:
        assert circle_info.counting_circle is not None
        try:
            # entity id
            entity_id_str = circle_info.counting_circle.counting_circle_id
            assert entity_id_str is not None
            entity_id = int(entity_id_str)
            entity_id = 0 if entity_id in EXPATS else entity_id
            assert entity_id == 0 or entity_id in entities

            # name and district
            line_errors: list[str] = []
            name, district, superregion = get_entity_and_district(
                entity_id, entities, vote, principal, line_errors
            )
            assert not line_errors

            # ballot result
            result = {
                'ballot_id': ballot.id,
                'entity_id': entity_id,
                'name': name,
                'district': district,
                'counted': False,
                'eligible_voters': 0,
                'expats': None,
                'invalid': 0,
                'empty': 0,
                'yeas': 0,
                'nays': 0,
            }

            # results (optional)
            result_data = circle_info.result_data
            if not result_data:
                status = 'interim'
            else:
                voters = result_data.count_of_voters_information
                assert voters is not None
                all_expats = [
                    subtotal.count_of_voters
                    for subtotal in voters.subtotal_info
                    if subtotal.voter_type == VoterTypeType.VALUE_2
                ]
                expats = all_expats[0] if all_expats else None
                assert expats is None or isinstance(expats, int)

                if not result_data.fully_counted_true:
                    status = 'interim'
                else:
                    result['eligible_voters'] = voters.count_of_voters_total
                    result['expats'] = expats
                    result['counted'] = result_data.fully_counted_true
                    result['invalid'] = result_data.received_invalid_votes or 0
                    result['empty'] = (
                        getattr(result_data, 'received_blank_votes', 0)
                        or getattr(result_data, 'received_empty_votes', 0)
                    )
                    result['yeas'] = result_data.count_of_yes_votes or 0
                    result['nays'] = result_data.count_of_no_votes or 0

        except (AssertionError, TypeError, ValueError):
            errors.append(
                FileImportError(
                    _('Invalid values'),
                    filename=identification,
                    line=entity_id_str  # type:ignore[arg-type]
                ),
            )
        else:
            results[entity_id] = result

    if not errors:
        # add the results to the DB
        existing = {result.entity_id: result for result in ballot.results}
        for result in results.values():
            assert isinstance(result['entity_id'], int)
            entity_id = result['entity_id']
            if entity_id in existing:
                for key, value in result.items():
                    if hasattr(existing[entity_id], key):
                        if getattr(existing[entity_id], key) != value:
                            setattr(existing[entity_id], key, value)
            else:
                ballot.results.append(BallotResult(**result))

        # remove obsolete results
        obsolete = set(existing.keys()) - set(results.keys())
        for entity_id in obsolete:
            ballot.results.remove(existing[entity_id])

        vote.status = status

    return vote, errors
