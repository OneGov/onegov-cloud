from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.translator_directory.models.certificate import LanguageCertificate


class LanguageCertificateCollection(GenericCollection[LanguageCertificate]):

    @property
    def model_class(self) -> type[LanguageCertificate]:
        return LanguageCertificate
