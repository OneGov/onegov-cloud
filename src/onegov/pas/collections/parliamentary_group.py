from __future__ import annotations

from onegov.parliament.collections.parliamentary_group import (
    ParliamentaryGroupCollection)
from onegov.pas.models import PASParliamentaryGroup


class PASParliamentaryGroupCollection(
    ParliamentaryGroupCollection[PASParliamentaryGroup]
):

    @property
    def model_class(self) -> type[PASParliamentaryGroup]:
        return PASParliamentaryGroup
