from onegov_testing.utils import create_app
from onegov.agency.app import AgencyApp
from onegov.agency.initial_content import create_new_organisation


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


def test_initial_content(request):
    app = create_app(AgencyApp, request, use_smtp=False)
    org = create_new_organisation(app, "Test", 'de_CH')

    assert org.locales == 'de_CH'
    assert org.name == "Test"
    assert ''.join([
        line.strip() for line in org.homepage_structure.splitlines()
    ]) == ''.join([
        line.strip() for line in homepage_structure.splitlines()
    ])
