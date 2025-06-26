from __future__ import annotations

from onegov.parliament.collections.parliamentary_group import (
    ParliamentaryGroupCollection)
from onegov.pas.models import PASParliamentaryGroup

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from onegov.parliament.models import ParliamentaryGroup


class PASParliamentaryGroupCollection(ParliamentaryGroupCollection):

    @property
    def model_class(self) -> type[ParliamentaryGroup]:
        return PASParliamentaryGroup
