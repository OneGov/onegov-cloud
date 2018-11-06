from onegov.agency.initial_content import create_new_organisation


homepage_structure = """<row>
  <column span="12">
    <panel>
      <links>
          <link url="./personen"
              description="Personen">
              Alle Personen
          </link>
          <link url="./organisationen"
              description="Organisationen">
              Alle Organisationen
          </link>
      </links>
    </panel>
  </column>
</row>"""


def test_initial_content(agency_app):
    org = create_new_organisation(agency_app, "Test", 'de_CH')

    assert org.locales == 'de_CH'
    assert org.name == "Test"
    assert ''.join([
        line.strip() for line in org.homepage_structure.splitlines()
    ]) == ''.join([
        line.strip() for line in homepage_structure.splitlines()
    ])
