from __future__ import annotations

from onegov.activity.models.publication_request import PublicationRequest
from onegov.core.collection import GenericCollection


class PublicationRequestCollection(GenericCollection[PublicationRequest]):

    @property
    def model_class(self) -> type[PublicationRequest]:
        return PublicationRequest
