from __future__ import annotations

from onegov.election_day import _
from onegov.election_day.formats.imports.common import convert_ech_domain
from onegov.election_day.formats.imports.common import EXPATS
from onegov.election_day.formats.imports.common import FileImportError
from onegov.election_day.formats.imports.common import get_entity_and_district
from onegov.election_day.models import Candidate
from onegov.election_day.models import CandidatePanachageResult
from onegov.election_day.models import CandidateResult
from onegov.election_day.models import Election
from onegov.election_day.models import ElectionCompound
from onegov.election_day.models import ElectionResult
from onegov.election_day.models import List
from onegov.election_day.models import ListConnection
from onegov.election_day.models import ListPanachageResult
from onegov.election_day.models import ListResult
from onegov.election_day.models import ProporzElection
from xsdata_ech.e_ch_0155_5_0 import ListRelationType
from xsdata_ech.e_ch_0155_5_0 import SexType
from xsdata_ech.e_ch_0155_5_0 import TypeOfElectionType
from xsdata_ech.e_ch_0252_1_0 import VoterTypeType as VoterTypeTypeV1
from xsdata_ech.e_ch_0252_2_0 import VoterTypeType as VoterTypeTypeV2

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from datetime import date
    from onegov.election_day.formats.imports.common import ECHImportResultType
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from onegov.election_day.types import Gender
    from sqlalchemy.orm import Session
    from typing import TypeAlias
    from xsdata_ech.e_ch_0252_2_0 import Delivery
    from xsdata_ech.e_ch_0252_2_0 import ElectedType
    from xsdata_ech.e_ch_0252_2_0 import ElectionResultType
    from xsdata_ech.e_ch_0252_2_0 import EventElectionInformationDeliveryType
    from xsdata_ech.e_ch_0252_2_0 import EventElectionResultDeliveryType

    MajoralElected: TypeAlias = ElectedType.MajoralElection.ElectedCandidate
    ProportionalElected: TypeAlias = (
        ElectedType.ProportionalElection.ListType.ElectedCandidate)


election_class = {
    TypeOfElectionType.VALUE_1: ProporzElection,
    TypeOfElectionType.VALUE_2: Election,
}

gender: dict[SexType, Gender] = {
    SexType.VALUE_1: 'male',
    SexType.VALUE_2: 'female',
    SexType.VALUE_3: 'undetermined',
}


def import_elections_ech(
    principal: Canton | Municipality,
    delivery: Delivery,
    session: Session,
    default_locale: str,
) -> ECHImportResultType:
    """ Imports all elections in a given eCH-0252 delivery.

    Deletes elections on the same day not appearing in the delivery.

    :return:
        A tuple consisting of a list with errors, a set with updated
        elections, and a set with deleted elections.

    """

    polling_day = None
    compounds: list[ElectionCompound] = []
    elections: list[Election] = []
    deleted: set[ElectionCompound | Election] = set()
    errors: set[FileImportError] = set()

    # process compounds, election, list and candidate information
    information_delivery = delivery.election_information_delivery
    if information_delivery:
        (
            polling_day,
            compounds,
            elections,
            deleted,
            errors
        ) = import_information_delivery(
            principal,
            information_delivery,
            session,
            default_locale,
        )

    # process election, candidate and list results
    result_delivery = delivery.election_result_delivery
    if result_delivery:
        # query elections
        assert result_delivery.polling_day
        if (
            not polling_day
            or (
                result_delivery.polling_day
                != information_delivery.polling_day  # type:ignore[union-attr]
            )
        ):
            assert result_delivery.polling_day is not None
            polling_day = result_delivery.polling_day.to_date()
            elections = session.query(Election).filter(
                Election.date == polling_day
            ).all()

        import_result_delivery(
            principal, result_delivery, session, polling_day, elections, errors
        )

    return (
        list(errors), compounds + elections, deleted
    )  # type:ignore[return-value]


def import_information_delivery(
    principal: Canton | Municipality,
    delivery: EventElectionInformationDeliveryType,
    session: Session,
    default_locale: str,
) -> tuple[
    date,
    list[ElectionCompound],
    list[Election],
    set[ElectionCompound | Election],
    set[FileImportError]
]:
    """ Import an election information delivery. """

    assert delivery is not None

    # get polling date and entities
    assert delivery.polling_day is not None
    polling_day = delivery.polling_day.to_date()
    entities = principal.entities[polling_day.year]
    errors = set()

    # query existing compounds
    existing_compounds = session.query(ElectionCompound).filter(
        ElectionCompound.date == polling_day
    ).all()

    # query existing elections
    existing_elections = session.query(Election).filter(
        Election.date == polling_day
    ).all()

    # process compounds
    compounds: dict[str, ElectionCompound] = {}
    for association in delivery.election_association:
        identification = association.election_association_id
        assert identification
        name = association.election_association_name
        assert name

        # get or create compound
        compound = None
        for existing_c in existing_compounds:
            if identification in (existing_c.external_id, existing_c.id):
                compound = existing_c
                break
        if not compound:
            compound = ElectionCompound(
                id=identification.lower(),
                external_id=identification,
                date=polling_day,
                domain='canton',
                title_translations={default_locale: name}
            )
            session.add(compound)
        compounds[identification] = compound

    # process elections
    elections: dict[str, Election] = {}
    for group_info in delivery.election_group_info:
        assert group_info.election_group
        group = group_info.election_group
        assert group.domain_of_influence
        supported, domain, _domain_segment = convert_ech_domain(
            group.domain_of_influence, principal, entities
        )
        if not supported:
            errors.add(
                FileImportError(
                    _('Domain not supported'),
                    filename=group.election_group_identification
                )
            )
            continue

        for information in group.election_information:
            assert information.election
            info = information.election
            assert info.election_identification
            identification = info.election_identification
            assert info.type_of_election
            cls = election_class[info.type_of_election]

            # get or create election
            election = None
            for existing_e in existing_elections:
                if identification in (existing_e.external_id, existing_e.id):
                    election = existing_e
                    break
            if not election:
                election = cls(
                    id=identification.lower(),
                    external_id=identification,
                    date=polling_day,
                    domain='federation',
                    title_translations={}
                )
                if not isinstance(election, ProporzElection):
                    election.majority_type = 'relative'
                session.add(election)
            if election.__class__ != cls:
                errors.add(
                    FileImportError(
                        _('Changing types is not supported'),
                        filename=identification
                    )
                )
                continue

            # update election
            elections[identification] = election
            election.domain = domain
            assert info.election_description
            title_translations = {}
            short_title_translations = {}
            for title in info.election_description.election_description_info:
                assert title.language
                assert title.election_description
                locale = f'{title.language.lower()}_CH'
                title_translations[locale] = title.election_description
                short_title_translations[locale] = (
                    title.election_description_short or ''
                )
            election.title_translations = title_translations
            election.short_title_translations = short_title_translations
            if info.election_position is not None:
                election.shortcode = str(info.election_position)
            election.number_of_mandates = info.number_of_mandates or 0
            compound_id = information.referenced_election_association_id
            if compound_id:
                compound = compounds[compound_id]
                election.election_compound_id = compound.id
            else:
                election.election_compound_id = None

            # update candidates
            existing_candidates = {
                candidate.candidate_id: candidate
                for candidate in election.candidates
            }
            candidates = {}
            for c_info in information.candidate:
                assert c_info.candidate_identification
                candidate_id = c_info.candidate_identification
                candidate = existing_candidates.get(candidate_id)
                if not candidate:
                    candidate = Candidate(
                        candidate_id=candidate_id,
                        elected=False
                    )
                    session.add(candidate)
                candidates[candidate_id] = candidate
                candidate.family_name = c_info.family_name or ''
                candidate.first_name = c_info.call_name or ''
                assert c_info.date_of_birth
                date_of_birth = c_info.date_of_birth.to_date()
                candidate.year_of_birth = date_of_birth.year
                assert c_info.sex
                candidate.gender = gender[c_info.sex]
                if c_info.party_affiliation:
                    names = {
                        f'{(party.language or "").lower()}_CH':
                        party.party_affiliation_short
                        for party
                        in c_info.party_affiliation.party_affiliation_info
                    }
                    candidate.party = names.get(default_locale)
            election.candidates = list(candidates.values())

            if not isinstance(election, ProporzElection):
                continue

            # update lists
            existing_lists = {
                list_.list_id: list_ for list_ in election.lists
            }
            lists = {}
            for l_info in information.list_value:
                assert l_info.list_identification
                list_id = l_info.list_identification
                list_ = existing_lists.get(list_id)
                if not list_:
                    list_ = List()
                    list_.list_id = list_id
                    list_.number_of_mandates = 0
                    list_.election = election
                    session.add(list_)
                lists[list_id] = list_
                assert l_info.list_description
                assert l_info.list_description.list_description_info
                names = {
                    f'{(name.language or "").lower()}_CH':
                    name.list_description
                    for name
                    in l_info.list_description.list_description_info
                }
                list_.name = names.get(default_locale, '') or ''
                if not list_.id:
                    # NOTE: This is required for SQLAlchemy to not get
                    #       confused about the order of add operations
                    #       since the list is referenced in many places
                    session.flush()
                    session.refresh(list_)
                for pos in l_info.candidate_position:
                    assert pos.candidate_identification
                    candidates[pos.candidate_identification].list = list_
            election.lists = list(lists.values())

            # update list connections
            existing_connections = {
                connection.connection_id: connection
                for connection in election.list_connections
            }
            connections = {}
            for union in information.list_union:
                assert union.list_union_identification
                connection_id = union.list_union_identification
                connection = existing_connections.get(connection_id)
                if not connection:
                    connection = ListConnection(
                        connection_id=connection_id
                    )
                    session.add(connection)
                connections[connection_id] = connection
                for list_id in union.referenced_list:
                    lists[list_id].connection = connection
            for union in information.list_union:
                if union.list_union_type != ListRelationType.VALUE_2:
                    continue
                assert union.list_union_identification
                connection_id = union.list_union_identification
                connection = connections[connection_id]
                assert union.referenced_list_union
                parent = connections[union.referenced_list_union]
                connection.parent = parent
            election.list_connections = list(connections.values())

    # delete obsolete compounds and elections
    deleted: set[ElectionCompound | Election] = set()
    deleted.update({
        compound for compound in existing_compounds
        if compound not in compounds.values()
    })
    deleted.update({
        election for election in existing_elections
        if election not in elections.values()
    })

    return (
        polling_day,
        list(compounds.values()),
        list(elections.values()),
        deleted,
        errors
    )


def import_result_delivery(
    principal: Canton | Municipality,
    delivery: EventElectionResultDeliveryType,
    session: Session,
    polling_day: date,
    elections: list[Election],
    errors: set[FileImportError]
) -> None:
    """ Import an election result delivery. """

    entities = principal.entities[polling_day.year]

    # process results
    for group_result in delivery.election_group_result:
        for result in group_result.election_result:
            assert result.election_identification
            identification = result.election_identification

            # get election
            election = None
            for existing in elections:
                if identification in (existing.external_id, existing.id):
                    election = existing
                    break
            if not election:
                errors.add(
                    FileImportError(
                        _('Election does not exist'),
                        filename=identification
                    )
                )
                continue

            # get candidates and lists
            candidates = {c.candidate_id: c for c in election.candidates}
            lists = {}
            if isinstance(election, ProporzElection):
                lists = {list_.list_id: list_ for list_ in election.lists}

            # update election results
            existing_election_results = {
                result.entity_id: result for result in election.results
            }
            election_results = {}
            assert result.counting_circle_result
            for circle in result.counting_circle_result:
                assert circle.counting_circle_id is not None
                entity_id = int(circle.counting_circle_id)
                entity_id = 0 if entity_id in EXPATS else entity_id
                if entity_id == 0:
                    election.has_expats = True
                election_result = existing_election_results.get(entity_id)
                if not election_result:
                    election_result = ElectionResult(
                        entity_id=entity_id
                    )
                    session.add(election_result)
                election_results[entity_id] = election_result

                name, district, superregion = get_entity_and_district(
                    entity_id, entities, election, principal
                )

                election_result.counted = circle.fully_counted_true or False
                election_result.name = name
                election_result.district = district
                election_result.superregion = superregion
                if not circle.fully_counted_true:
                    election_result.eligible_voters = 0
                    election_result.received_ballots = 0
                    election_result.blank_ballots = 0
                    election_result.invalid_ballots = 0
                    election_result.invalid_votes = 0
                    election_result.blank_votes = 0
                else:
                    assert circle.count_of_voters_information
                    election_result.eligible_voters = (
                        circle
                        .count_of_voters_information
                        .count_of_voters_total or 0)
                    expats = [
                        subtotal.count_of_voters
                        for subtotal
                        in circle.count_of_voters_information.subtotal_info
                        if (
                            subtotal.voter_type in (
                                VoterTypeTypeV1.VALUE_2,
                                VoterTypeTypeV2.VALUE_2
                            )
                            and subtotal.sex is None
                        )
                    ]
                    election_result.expats = expats[0] if expats else None
                    election_result.received_ballots = (
                        circle.count_of_received_ballots or 0)
                    election_result.blank_ballots = (
                        circle.count_of_blank_ballots or 0)
                    election_result.invalid_ballots = (
                        circle.count_of_invalid_ballots or 0)
                    assert circle.election_result
                    if circle.election_result.majoral_election:
                        import_majoral_election_result(
                            session,
                            candidates,
                            election_result,
                            circle.election_result.majoral_election,
                            errors
                        )
                    if circle.election_result.proportional_election:
                        import_proportional_election_result(
                            session,
                            candidates,
                            lists,
                            election_result,
                            circle.election_result.proportional_election,
                            errors
                        )

            # add the missing entities
            remaining = set(entities.keys())
            if election.has_expats:
                remaining.add(0)
            remaining -= set(election_results.keys())
            for entity_id in remaining:
                name, district, superregion = get_entity_and_district(
                    entity_id, entities, election, principal
                )
                if election.domain == 'none':
                    continue
                if election.domain == 'municipality':
                    if principal.domain != 'municipality':
                        if name != election.domain_segment:
                            continue
                election_results[entity_id] = ElectionResult(
                    entity_id=entity_id,
                    name=name,
                    district=district,
                    superregion=superregion,
                    counted=False
                )

            # add the results and update the status
            election.results = list(election_results.values())
            counted = all(result.counted for result in election.results)
            election.status = 'final' if counted else 'interim'
            election.last_result_change = election.timestamp()

            # Aggregate candidate panachage to list panachage
            list_panachage: dict[List, dict[List | None, int]] = {}
            for candidate in election.candidates:
                for panachage_result in candidate.panachage_results:
                    source = panachage_result.list
                    target = panachage_result.candidate.list
                    if target is None or source == target:
                        continue
                    list_panachage.setdefault(target, {})
                    list_panachage[target].setdefault(source, 0)
                    list_panachage[target][source] += panachage_result.votes
            for target, sources in list_panachage.items():
                target.panachage_results = []
                for source, votes in sources.items():
                    lpanachage_result = ListPanachageResult(votes=votes)
                    session.add(lpanachage_result)
                    lpanachage_result.target = target
                    if source:
                        lpanachage_result.source = source
                    target.panachage_results.append(lpanachage_result)

            # update absolute majority and elected candidates
            election.absolute_majority = None
            for candidate in candidates.values():
                candidate.elected = False
            elected_candidates: list[MajoralElected | ProportionalElected] = []

            if result.elected:
                if result.elected.majoral_election:
                    majoral = result.elected.majoral_election
                    elected_candidates = (
                        majoral.elected_candidate)  # type:ignore[assignment]

                    absolute_majority = majoral.absolute_majority
                    if absolute_majority is not None:
                        election.majority_type = 'absolute'
                    election.absolute_majority = absolute_majority

                if result.elected.proportional_election:
                    proportional = result.elected.proportional_election
                    for list_v in proportional.list_value:
                        list_id = list_v.list_identification or ''
                        list_ = get_list(lists, list_id, errors)
                        if not list_:
                            continue
                        list_.number_of_mandates = len(
                            list_v.elected_candidate
                        )
                        elected_candidates.extend(list_v.elected_candidate)

            for elected in elected_candidates:
                candidate_id = elected.candidate_identification or ''
                e_candidate = get_candidate(candidates, candidate_id, errors)
                if e_candidate:
                    e_candidate.elected = True


def import_majoral_election_result(
    session: Session,
    candidates: dict[str, Candidate],
    election_result: ElectionResult,
    majoral_election: ElectionResultType.MajoralElection,
    errors: set[FileImportError]
) -> None:
    """ Helper function to import election results specific to majoral
    elections.

    """
    election_result.invalid_votes = (
        majoral_election.count_of_invalid_votes_total or 0)
    election_result.blank_votes = (
        majoral_election.count_of_blank_votes_total or 0)

    existing_candidate_results = {
        result.candidate.candidate_id: result
        for result in election_result.candidate_results
    }
    candidate_results = {}
    for result in majoral_election.candidate_result:
        candidate_id = result.candidate_identification or ''
        candidate = get_candidate(candidates, candidate_id, errors)
        if not candidate:
            return
        candidate_result = existing_candidate_results.get(candidate_id)
        if not candidate_result:
            candidate_result = CandidateResult(candidate_id=candidate.id)
            session.add(candidate_result)
        candidate_results[candidate_id] = candidate_result
        candidate_result.votes = result.count_of_votes_total or 0

    election_result.candidate_results = list(candidate_results.values())


def import_proportional_election_result(
    session: Session,
    candidates: dict[str, Candidate],
    lists: dict[str, List],
    election_result: ElectionResult,
    proportional_election: ElectionResultType.ProportionalElection,
    errors: set[FileImportError]
) -> None:
    """ Helper function to import election results specific to proportional
    elections.

    """
    election_result.invalid_votes = 0
    election_result.blank_votes = (
        proportional_election
        .count_of_empty_votes_of_changed_ballots_without_list_designation or 0)

    existing_candidate_results = {
        result.candidate.candidate_id: result
        for result in election_result.candidate_results
    }
    candidate_results = {}
    candidate_panachage_results = election_result.candidate_panachage_results
    existing_list_results = {
        result.list.list_id: result
        for result in election_result.list_results
    }
    list_results = {}

    # election_result
    for l_result in proportional_election.list_results:
        # List result
        list_id = l_result.list_identification or ''
        list_ = get_list(lists, list_id, errors)
        if not list_:
            return
        list_result = existing_list_results.get(list_id)
        if not list_result:
            list_result = ListResult(list_id=list_.id)
            session.add(list_result)
        list_results[list_id] = list_result
        list_result.votes = l_result.count_of_candidate_votes or 0

        # Candidate results
        for c_result in l_result.candidate_results:
            candidate_id = c_result.candidate_identification or ''
            candidate = get_candidate(candidates, candidate_id, errors)
            if not candidate:
                return
            candidate_result = existing_candidate_results.get(candidate_id)
            if not candidate_result:
                candidate_result = CandidateResult(candidate_id=candidate.id)
                session.add(candidate_result)
            candidate_results[candidate_id] = candidate_result
            candidate_result.votes = (
                (c_result.count_of_votes_from_unchanged_ballots or 0)
                + (c_result.count_of_votes_from_changed_ballots or 0)
            )

            # Panachage
            p_result = c_result.candidate_list_results_info
            if not p_result:
                continue

            existing_panachage_results = {
                getattr(result.list, 'list_id', ''): result
                for result in candidate_panachage_results
                if result.candidate == candidate
            }
            panachage_results = {}

            # ... blank
            panachage_result = existing_panachage_results.get('')
            if not panachage_result:
                panachage_result = CandidatePanachageResult()
                session.add(panachage_result)
                panachage_result.election_result = election_result
                panachage_result.candidate = candidate
            panachage_results[''] = panachage_result
            panachage_result.votes = (
                p_result
                .count_of_votes_from_ballots_without_list_designation or 0)

            # ... lists
            for source in p_result.candidate_list_results:
                assert source.list_identification
                source_id = source.list_identification
                source_list = get_list(lists, source_id, errors)
                if not source_list:
                    return
                panachage_result = existing_panachage_results.get(source_id)
                if not panachage_result:
                    panachage_result = CandidatePanachageResult()
                    session.add(panachage_result)
                    panachage_result.election_result = election_result
                    panachage_result.candidate = candidate
                    panachage_result.list = source_list
                panachage_results[source_id] = panachage_result
                panachage_result.votes = (
                    source.count_of_votes_from_changed_ballots or 0)

            # ... remove obsolete
            obsolete = set(existing_panachage_results) - set(panachage_results)
            for list_id in obsolete:
                election_result.candidate_panachage_results.remove(
                    existing_panachage_results[list_id]
                )

    election_result.candidate_results = list(candidate_results.values())
    election_result.list_results = list(list_results.values())


def get_candidate(
    candidates: dict[str, Candidate],
    candidate_id: str,
    errors: set[FileImportError]
) -> Candidate | None:
    """ Helper function to retreive a candidate of existing candidates. """

    candidate = candidates.get(candidate_id)
    if not candidate:
        errors.add(
            FileImportError(
                _('Candidate does not exist'),
                filename=candidate_id
            )
        )
    return candidate


def get_list(
    lists: dict[str, List],
    list_id: str,
    errors: set[FileImportError]
) -> List | None:
    """ Helper function to retreive a list of existing lists. """

    list_ = lists.get(list_id)
    if not list_:
        errors.add(
            FileImportError(
                _('List does not exist'),
                filename=list_id
            )
        )
    return list_
