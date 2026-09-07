from __future__ import annotations

from onegov.core.collection import GenericCollection
from onegov.translator_directory.models.certificate import LanguageCertificate

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from uuid import UUID  # ruff:ignore[unused-import]


class LanguageCertificateCollection(
    GenericCollection[LanguageCertificate, 'UUID']
):

    @property
    def model_class(self) -> type[LanguageCertificate]:
        return LanguageCertificate
