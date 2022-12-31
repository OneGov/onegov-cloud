from onegov.ballot import ComplexVote
from onegov.ballot import Election
from onegov.ballot import ElectionCompound
from onegov.ballot import ElectionCompoundPart
from onegov.ballot import ProporzElection
from onegov.ballot import Vote
from onegov.core.utils import Bunch
from onegov.election_day.layouts.detail import DetailLayout
from onegov.election_day.models import Principal
from tests.onegov.election_day.common import DummyRequest
from textwrap import dedent


def test_hidden_tabs_mixin():
    principal = Principal.from_yaml(dedent("""
            name: Kanton St. Gallen
            canton: sg
            hidden_elements:
              tabs:
                elections:
                  - party-panachage
                elections-part:
                  - party-strengths
                election:
                  - statistics
                vote:
                  - districts
        """))
    request = DummyRequest()
    request.app.principal = principal

    for model, tab in (
        (Vote(), 'districts'),
        (ComplexVote(), 'districts'),
        (Election(), 'statistics'),
        (ProporzElection(), 'statistics'),
        (ElectionCompound(), 'party-panachage'),
        (ElectionCompoundPart(Bunch(id='1'), 'x', 'y'), 'party-strengths'),
    ):
        layout = DetailLayout(model, request)
        assert layout.hide_tab(tab) is True
