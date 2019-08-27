from onegov.election_day.utils.common import add_cors_header
from onegov.election_day.utils.common import add_last_modified_header
from onegov.election_day.utils.common import add_local_results
from onegov.election_day.utils.filenames import pdf_filename
from onegov.election_day.utils.filenames import svg_filename
from onegov.election_day.utils.summaries import get_election_compound_summary
from onegov.election_day.utils.summaries import get_election_summary
from onegov.election_day.utils.summaries import get_summaries
from onegov.election_day.utils.summaries import get_summary
from onegov.election_day.utils.summaries import get_vote_summary


__all__ = [
    'add_cors_header',
    'add_last_modified_header',
    'add_local_results',
    'get_election_compound_summary',
    'get_election_summary',
    'get_summaries',
    'get_summary',
    'get_vote_summary',
    'pdf_filename',
    'svg_filename',
]
