from __future__ import annotations

from onegov.agency.app import AgencyApp
from onegov.agency.initial_content import create_new_organisation
from tests.shared.utils import create_app


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import pytest


homepage_structure = """<row>
  <column span="12">
    <panel>
      <links>
          <link url="./people"
              description="Personen">
              Alle Personen
          </link>
          <link url="./organizations"
              description="Organisationen">
              Alle Organisationen
          </link>
      </links>
    </panel>
  </column>
</row>"""


def test_initial_content(request: pytest.FixtureRequest) -> None:
    app = create_app(
        AgencyApp,
        request,
        use_maildir=False,
        websockets={
            'client_url': 'ws://localhost:8766',
            'manage_url': 'ws://localhost:8766',
            'manage_token': 'super-super-secret-token'
        }
    )
    org = create_new_organisation(app, "Test", 'de_CH')

    assert org.locales == 'de_CH'
    assert org.name == "Test"
    assert org.homepage_structure is not None
    assert '\n'.join(
        line.strip() for line in org.homepage_structure.splitlines()
    ) == '\n'.join(
        line.strip() for line in homepage_structure.splitlines()
    )
