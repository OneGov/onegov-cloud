import json
from datetime import date

import pytest
from onegov.ballot import Election, ProporzElection
from onegov.core.utils import module_path
from onegov.election_day.utils.election.lists import \
    get_aggregated_list_results
from tests.onegov.election_day.common import import_wabstic_data


# @pytest.mark.parametrize("tar_file", [
#     module_path('tests.onegov.election_day',
#                 'fixtures/WP-Dateien_NR2019_Zwischenresultate.tar.gz'),
# ])
def test_get_aggregated_list_results(election_day_app_sg, tar_file):
    session = election_day_app_sg.session_manager.session()
    session.add(
        ProporzElection(
            title='NR2019',
            domain='federation',
            date=date(2019, 10, 20),
            number_of_mandates=12,
            expats=True
        )
    )
    session.flush()
    election = session.query(Election).one()
    data = get_aggregated_list_results(election, session)['results']
    assert data == []

    # Load results
    # import_wabstic_data(
    #     election, tar_file, election_day_app_sg.principal, expats=True
    # )

    print(json.dumps(data, indent=2))
    assert False



