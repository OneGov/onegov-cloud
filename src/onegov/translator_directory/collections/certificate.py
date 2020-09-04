from onegov.core.collection import GenericCollection
from onegov.translator_directory.models.certificate import LanguageCertificate


class LanguageCertificateCollection(GenericCollection):

    @property
    def model_class(self):
        return LanguageCertificate
