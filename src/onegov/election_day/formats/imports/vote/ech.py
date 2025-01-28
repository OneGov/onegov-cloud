from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.formats.imports.common import convert_ech_domain
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from onegov.election_day.models import Ballot
from onegov.election_day.models import BallotResult
from onegov.election_day.models import ComplexVote
from onegov.election_day.models import Vote
from sqlalchemy.orm import joinedload
from xsdata_ech.e_ch_0252_1_0 import VoterTypeType as VoterTypeTypeV1
from xsdata_ech.e_ch_0252_2_0 import VoterTypeType as VoterTypeTypeV2
from xsdata_ech.e_ch_0252_1_0 import VoteSubTypeType as VoteSubTypeTypeV1
from xsdata_ech.e_ch_0252_2_0 import VoteSubTypeType as VoteSubTypeTypeV2

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.formats.imports.common import ECHImportResultType
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from sqlalchemy.orm import Session
    from xsdata_ech.e_ch_0252_1_0 import Delivery as DeliveryV1
    from xsdata_ech.e_ch_0252_2_0 import Delivery as DeliveryV2


def import_votes_ech(
    principal: Canton | Municipality,
    delivery: DeliveryV1 | DeliveryV2,
    session: Session
) -> ECHImportResultType:
    """ Imports all votes in a given eCH-0252 delivery.

    Deletes votes on the same day not appearing in the delivery.

    :return:
        A tuple consisting of a list with errors, a set with updated
        votes, and a set with deleted votes.

    """

    if not delivery.vote_base_delivery:
        return [], set(), set()

    vote_base_delivery = delivery.vote_base_delivery
    assert vote_base_delivery.polling_day is not None
    polling_day = vote_base_delivery.polling_day.to_date()
    entities = principal.entities[polling_day.year]

    # extract vote and ballot structure
    classes: dict[str, type[Vote | ComplexVote]] = {}
    for vote_info in vote_base_delivery.vote_info:
        assert vote_info.vote
        sub_type = vote_info.vote.vote_sub_type
        if sub_type in (
            VoteSubTypeTypeV1.VALUE_1, VoteSubTypeTypeV2.VALUE_1
        ):
            classes.setdefault(vote_info.vote.vote_identification or '', Vote)
        elif sub_type in (
            VoteSubTypeTypeV1.VALUE_2, VoteSubTypeTypeV2.VALUE_2,
            VoteSubTypeTypeV1.VALUE_3, VoteSubTypeTypeV2.VALUE_3
        ):
            classes[vote_info.vote.main_vote_identification or ''] = (
                ComplexVote)

    # get or create votes
    existing_votes = session.query(Vote).filter(
        Vote.date == polling_day
    ).options(joinedload(Vote.ballots, Ballot.results)).all()
    votes = {}
    for identification, cls in classes.items():
        vote = None
        for existing in existing_votes:
            if identification in (existing.external_id, existing.id):
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
                FileImportError(_('Changing types is not supported'))
            ], set(), set()
        votes[identification] = vote

    # delete obsolete votes
    deleted = {vote for vote in existing_votes if vote not in votes.values()}

    # update information and add results
    errors = []
    for vote_info in vote_base_delivery.vote_info:

        # titles and domain
        assert vote_info.vote
        identification = (
            vote_info.vote.main_vote_identification
            or vote_info.vote.vote_identification
            or ''
        )
        title_translations = {}
        short_title_translations = {}
        for title in vote_info.vote.vote_title_information:
            assert title.language
            assert title.vote_title
            locale = f'{title.language.lower()}_CH'
            title_translations[locale] = title.vote_title
            short_title_translations[locale] = title.vote_title_short or ''
        vote = votes[identification]
        ballot = vote.proposal
        if vote_info.vote.vote_sub_type in (
            VoteSubTypeTypeV1.VALUE_1, VoteSubTypeTypeV2.VALUE_1
        ):
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
            vote.short_title_translations = short_title_translations
            if vote_info.vote.sequence is not None:
                vote.shortcode = str(vote_info.vote.sequence)
        elif vote_info.vote.vote_sub_type in (
            VoteSubTypeTypeV1.VALUE_2, VoteSubTypeTypeV2.VALUE_2
        ):
            assert isinstance(vote, ComplexVote)
            vote.counter_proposal.title_translations = title_translations
            ballot = vote.counter_proposal
        elif vote_info.vote.vote_sub_type in (
            VoteSubTypeTypeV1.VALUE_3, VoteSubTypeTypeV2.VALUE_3
        ):
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

        # results
        existing_ballot_results = {
            result.entity_id: result for result in ballot.results
        }
        ballot_results = {}
        for circle_info in vote_info.counting_circle_info:
            assert circle_info.counting_circle is not None
            assert circle_info.counting_circle.counting_circle_id is not None

            # entity id
            entity_id = int(circle_info.counting_circle.counting_circle_id)
            entity_id = 0 if entity_id in EXPATS else entity_id
            ballot_result = existing_ballot_results.get(entity_id)
            if not ballot_result:
                ballot_result = BallotResult(entity_id=entity_id)
            ballot_results[entity_id] = ballot_result

            # name and district
            name, district, _superregion = get_entity_and_district(
                entity_id, entities, vote, principal
            )
            ballot_result.name = name
            ballot_result.district = district

            # results (optional)
            ballot_result.counted = False
            ballot_result.eligible_voters = 0
            ballot_result.expats = None
            ballot_result.invalid = 0
            ballot_result.empty = 0
            ballot_result.yeas = 0
            ballot_result.nays = 0
            if (
                circle_info.result_data
                and circle_info.result_data.fully_counted_true
            ):
                ballot_result.counted = True
                result_data = circle_info.result_data
                assert result_data.count_of_voters_information
                ballot_result.eligible_voters = (
                    result_data.count_of_voters_information
                    .count_of_voters_total or 0)
                expats = [
                    subtotal.count_of_voters
                    for subtotal
                    in result_data.count_of_voters_information.subtotal_info
                    if (
                        subtotal.voter_type in (
                            VoterTypeTypeV1.VALUE_2, VoterTypeTypeV2.VALUE_2
                        )
                        and subtotal.sex is None
                    )
                ]
                ballot_result.expats = expats[0] if expats else None
                ballot_result.invalid = result_data.received_invalid_votes or 0
                ballot_result.empty = (
                    getattr(result_data, 'received_blank_votes', 0)
                    or getattr(result_data, 'received_empty_votes', 0)
                )
                ballot_result.yeas = result_data.count_of_yes_votes or 0
                ballot_result.nays = result_data.count_of_no_votes or 0

        # add missing the missing entitites
        remaining = set(entities.keys())
        if vote.has_expats:
            remaining.add(0)
        remaining -= set(ballot_results.keys())
        for entity_id in remaining:
            name, district, _superregion = get_entity_and_district(
                entity_id, entities, vote, principal
            )
            if vote.domain == 'none':
                continue
            if vote.domain == 'municipality':
                if principal.domain != 'municipality':
                    if name != vote.domain_segment:
                        continue
            ballot_results[entity_id] = BallotResult(
                entity_id=entity_id,
                name=name,
                district=district,
                counted=False
            )

        # add the results and update the status
        ballot.results = list(ballot_results.values())
        counted = all(result.counted for result in ballot.results)
        vote.status = 'final' if counted else 'interim'
        vote.last_result_change = vote.timestamp()

    return errors, set(votes.values()), deleted
