from textwrap import dedent

from onegov.ballot import ElectionCompound, Election, Vote
from onegov.election_day.layouts.detail import DetailLayout
from onegov.election_day.models import Principal
from tests.onegov.election_day.common import DummyRequest


def test_hidden_tabs_mixin():
    principal = Principal.from_yaml(dedent("""
            name: Kanton St. Gallen
            canton: sg
            hidden_elements:
              tabs:
                elections:
                  - lists
                vote:
                  - districts
                election:
                  - statistics
        """))
    request = DummyRequest()
    request.app.principal = principal

    class DummyObject:
        def __init__(self, model):
            self.__tablename__ = model.__tablename__

    for model, tab in (
            (Vote, 'districts'),
            (Election, 'statistics'),
            (ElectionCompound, 'lists')
    ):
        layout = DetailLayout(DummyObject(model), request)
        assert layout.hide_tab(tab) is True

