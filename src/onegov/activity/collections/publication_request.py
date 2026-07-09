from __future__ import annotations

from onegov.activity.models.publication_request import PublicationRequest
from onegov.core.collection import GenericCollection

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from uuid import UUID  # noqa: F401


class PublicationRequestCollection(
    GenericCollection[PublicationRequest, 'UUID']
):

    @property
    def model_class(self) -> type[PublicationRequest]:
        return PublicationRequest
