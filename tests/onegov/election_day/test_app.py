from __future__ import annotations


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .conftest import TestApp


def test_principal_app_cache(election_day_app_zg: TestApp) -> None:
    assert election_day_app_zg.principal.name == "Kanton Govikon"
    assert election_day_app_zg.filestorage is not None
    election_day_app_zg.filestorage.remove('principal.yml')
    assert election_day_app_zg.principal.name == "Kanton Govikon"


def test_principal_app_not_existant(election_day_app_zg: TestApp) -> None:
    assert election_day_app_zg.filestorage is not None
    election_day_app_zg.filestorage.remove('principal.yml')
    assert election_day_app_zg.principal is None
