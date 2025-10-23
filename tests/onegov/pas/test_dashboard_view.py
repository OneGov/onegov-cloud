from __future__ import annotations


from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from tests.shared import Client
    from .conftest import TestPasApp

def test_view_dashboard_as_parliamentarian(client: Client[TestPasApp]) -> None:
    # FIXME: implement me
    pass
