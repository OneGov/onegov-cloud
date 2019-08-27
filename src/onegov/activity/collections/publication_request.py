from onegov.activity.models.publication_request import PublicationRequest
from onegov.core.collection import GenericCollection


class PublicationRequestCollection(GenericCollection):

    @property
    def model_class(self):
        return PublicationRequest
