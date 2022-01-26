def get_ballot_data_by_entity(ballot):
    """ Returns the yeas/nays percentage by entity_id. """

    data = {}
    for result in ballot.results:
        entity = {'counted': result.counted}
        if result.counted:
            entity['percentage'] = result.yeas_percentage
        data[result.entity_id] = entity

    return data


def get_ballot_data_by_district(ballot):
    """ Returns the yeas/nays percentage grouped and keyed by district. """

    data = {}
    for result in ballot.results_by_district:
        district = {
            'counted': result.counted,
            'entities': result.entity_ids
        }
        if result.counted:
            district['percentage'] = result.yeas_percentage
        data[result.name] = district

    return data
