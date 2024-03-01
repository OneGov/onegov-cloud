from onegov.ballot import Candidate
from onegov.ballot import Election
from onegov.ballot import List
from onegov.ballot import ListConnection
from onegov.ballot import ProporzElection
from onegov.election_day import _
from onegov.election_day.formats.imports.common import convert_ech_domain
from onegov.election_day.formats.imports.common import FileImportError
from xsdata_ech.e_ch_0155_5_0 import ListRelationType
from xsdata_ech.e_ch_0155_5_0 import SexType
from xsdata_ech.e_ch_0155_5_0 import TypeOfElectionType

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.ballot import Vote
    from onegov.ballot.types import Gender
    from onegov.election_day.formats.imports.common import ECHImportResultType
    from onegov.election_day.models import Canton
    from onegov.election_day.models import Municipality
    from sqlalchemy.orm import Session
    from xsdata_ech.e_ch_0252_2_0 import Delivery


election_class = {
    TypeOfElectionType.VALUE_1: ProporzElection,
    TypeOfElectionType.VALUE_2: Election,
}

gender: dict[SexType, 'Gender'] = {
    SexType.VALUE_1: 'male',
    SexType.VALUE_2: 'female',
    SexType.VALUE_3: 'undetermined',
}


def import_elections_ech(
    principal: 'Canton | Municipality',
    delivery: 'Delivery',
    session: 'Session',
    default_locale: str,
) -> 'ECHImportResultType':
    """ Imports all elections in a given eCH-0252 delivery.

    Deletes elections on the same day not appearing in the delivery.

    :return:
        A tuple consisting of a list with errors, a set with updated
        elections, and a set with deleted elections.

    """

    polling_day = None
    elections: dict[str, Election] = {}
    deleted: set['Election | Vote'] = set()
    errors = []

    # process election, list and candidate information
    if delivery.election_information_delivery:
        information_delivery = delivery.election_information_delivery
        assert information_delivery.polling_day is not None
        polling_day = information_delivery.polling_day.to_date()
        entities = principal.entities[polling_day.year]

        # query existing elections
        existing_elections = session.query(Election).filter(
            Election.date == polling_day
        ).all()  # todo: maybe add .options(joinedload().all()

        # process elections
        elections = {}
        for group_info in information_delivery.election_group_info:
            assert group_info.election_group
            group = group_info.election_group
            assert group.domain_of_influence
            supported, domain, domain_segment = convert_ech_domain(
                group.domain_of_influence, principal, entities
            )
            if not supported:
                errors.append(
                    FileImportError(
                        _('Domain not supported'),
                        filename=group.election_group_identification
                    )
                )
                continue

            # todo: group_info.counting_circle should be in the results
            # todo: is majority type in the results

            for information in group.election_information:
                assert information.election
                info = information.election
                assert info.election_identification
                identification = info.election_identification
                assert info.type_of_election
                cls = election_class[info.type_of_election]

                # get or create election
                election = None
                for existing in existing_elections:
                    if identification in (existing.id, existing.external_id):
                        election = existing
                        break
                if not election:
                    election = cls(
                        id=identification.lower(),
                        external_id=identification,
                        date=polling_day,
                        domain='federation',
                        title_translations={}
                    )
                    session.add(election)
                if not isinstance(election, cls):
                    errors.append(  # type:ignore[unreachable]
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
                titles = info.election_description.election_description_info
                election.title_translations = {
                    f'{title.language.lower()}_CH': title.election_description
                    for title in titles
                    if title.election_description and title.language
                }
                if info.election_position is not None:
                    election.shortcode = str(info.election_position)
                election.number_of_mandates = info.number_of_mandates or 0

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
                        list_ = List(list_id=list_id, number_of_mandates=0)
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
                    connections[connection_id] = connection
                    for list_id in union.referenced_list:
                        lists[list_id].connection = connection
                for union in information.list_union:
                    if not union.list_union_type == ListRelationType.VALUE_2:
                        continue
                    assert union.list_union_identification
                    connection_id = union.list_union_identification
                    connection = connections[connection_id]
                    assert union.referenced_list_union
                    parent = connections[union.referenced_list_union]
                    connection.parent = parent
                election.list_connections = list(connections.values())

        # delete obsolete elections
        deleted = {
            election for election in existing_elections
            if election not in elections.values()
        }

    # process results
    if delivery.election_result_delivery:
        # todo: parse polling_day, compare if set above

        # todo: query elections or use from above
        pass

    return [], set(elections.values()), deleted
