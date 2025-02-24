from __future__ import annotations

from onegov.pas.importer.json_import import PeopleImporter
from onegov.pas.models import (
    Parliamentarian
)


def test_people_importer_successful_import(session, people_json):
    importer = PeopleImporter(session)
    parliamentarian_map = importer.bulk_import(people_json['results'])

    parliamentarians = session.query(Parliamentarian).all()
    assert len(parliamentarians) == len(people_json)  # Assert correct number imported
    # ... more assertions to check specific parliamentarian attributes ...
