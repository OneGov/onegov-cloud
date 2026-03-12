from __future__ import annotations

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.election_day.models import Ballot
    from typing_extensions import TypedDict
    from typing import NotRequired

    class EntityData(TypedDict):
        counted: bool
        percentage: NotRequired[float]

    class DistrictData(EntityData):
        entities: list[int]


def get_ballot_data_by_entity(ballot: Ballot) -> dict[int, EntityData]:
    """ Returns the yeas/nays percentage by entity_id. """

    data = {}
    for result in ballot.results:
        entity: EntityData = {'counted': result.counted}
        if result.counted:
            entity['percentage'] = result.yeas_percentage
        data[result.entity_id] = entity

    return data


def get_ballot_data_by_district(ballot: Ballot) -> dict[str, DistrictData]:
    """ Returns the yeas/nays percentage grouped and keyed by district. """

    data = {}
    for result in ballot.results_by_district:
        district: DistrictData = {
            'counted': result.counted,
            'entities': result.entity_ids
        }
        if result.counted:
            district['percentage'] = result.yeas_percentage
        data[result.name] = district

    return data
