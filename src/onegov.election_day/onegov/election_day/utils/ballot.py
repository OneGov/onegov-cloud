def get_ballot_data_by_entity(ballot):
    """ Returns the yeas/nays percentage by entity_id.

    Uncounted entities are not included.

    """

    data = {}
    for result in ballot.results:
        entity = {'counted': result.counted}
        if result.counted:
            entity['yeas_percentage'] = result.yeas_percentage
            entity['nays_percentage'] = result.nays_percentage
        data[result.entity_id] = entity

    return data


def get_ballot_data_by_district(ballot):
    """ Returns the yeas/nays percentage grouped and keyed by district.

    Uncounted entities are not included.

    """

    data = {}
    for result in ballot.results_by_district:
        district = {
            'counted': result.counted,
            'municipalities': result.entity_ids
        }
        if result.counted:
            district['yeas_percentage'] = result.yeas_percentage
            district['nays_percentage'] = result.nays_percentage
        data[result.name] = district

    return data
