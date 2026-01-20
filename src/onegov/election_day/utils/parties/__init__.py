from __future__ import annotations

from onegov.election_day.utils.parties.parties import get_party_results
from onegov.election_day.utils.parties.parties import get_party_results_deltas
from onegov.election_day.utils.parties.parties import get_party_results_data
from onegov.election_day.utils.parties.parties import (
    get_party_results_seat_allocation)
from onegov.election_day.utils.parties.parties import (
    get_party_results_vertical_data)
from onegov.election_day.utils.parties.parties import (
    get_parties_panachage_data)


__all__ = (
    'get_parties_panachage_data',
    'get_party_results_data',
    'get_party_results_deltas',
    'get_party_results_seat_allocation',
    'get_party_results_vertical_data',
    'get_party_results',
)
