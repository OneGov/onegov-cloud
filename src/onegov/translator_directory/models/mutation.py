from __future__ import annotations

from functools import cached_property
from onegov.gis import Coordinates
from onegov.translator_directory import _
from onegov.translator_directory.constants import ADMISSIONS
from onegov.translator_directory.constants import field_order
from onegov.translator_directory.constants import GENDERS
from onegov.translator_directory.constants import INTERPRETING_TYPES
from onegov.translator_directory.constants import PROFESSIONAL_GUILDS
from onegov.translator_directory.models.translator import Translator


from typing import Any, ClassVar, TYPE_CHECKING
if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from onegov.ticket import Ticket
    from onegov.translator_directory.collections.language import (
        LanguageCollection)
    from onegov.translator_directory.collections.certificate import (
        LanguageCertificateCollection)
    from onegov.translator_directory.request import TranslatorAppRequest
    from sqlalchemy.orm import Session
    from translationstring import TranslationString
    from uuid import UUID


_missing = object()


class TranslatorMutation:

    def __init__(
        self,
        session: Session,
        target_id: UUID,
        ticket_id: UUID
    ) -> None:
        self.session = session
        self.target_id = target_id
        self.ticket_id = ticket_id

    @cached_property
    def language_collection(self) -> LanguageCollection:
        from onegov.translator_directory.collections.language import (
            LanguageCollection)
        return LanguageCollection(self.session)

    @cached_property
    def certificate_collection(self) -> LanguageCertificateCollection:
        from onegov.translator_directory.collections.certificate import (
            LanguageCertificateCollection)
        return LanguageCertificateCollection(self.session)

    # FIXME: Should we force that both the ticket and translator exist?
    #        Rather than do the check everywhere else?
    @cached_property
    def target(self) -> Translator | None:
        return self.session.query(Translator).filter_by(
            id=self.target_id
        ).first()

    @cached_property
    def ticket(self) -> Ticket | None:
        from onegov.ticket import TicketCollection
        return TicketCollection(self.session).by_id(self.ticket_id)

    @cached_property
    def changes(self) -> dict[str, Any]:
        assert self.ticket is not None
        handler_data = self.ticket.handler_data['handler_data']
        result = handler_data.get('proposed_changes', {})
        return {k: v for k, v in result.items() if hasattr(self.target, k)}

    def translated(
        self,
        request: TranslatorAppRequest,
        changes: dict[str, Any] | None = None
    ) -> dict[str, tuple[str, Any, Any]]:

        self.session = self.session or request.session

        def label(name: str) -> str:
            return request.translate(self.labels.get(name, name))

        def convert(name: str, value: Any) -> Any:
            if isinstance(value, Coordinates):
                return f'{value.lat}, {value.lon}'

            translations = self.translations.get(name)
            if translations:
                if isinstance(value, (list, tuple)):
                    return ', '.join(
                        request.translate(translations.get(v, v))
                        for v in value
                    )
                return request.translate(translations.get(value, value))

            if isinstance(value, list):
                return ', '.join(value)

            return value

        result = sorted(
            (
                (key, (label(key), convert(key, value), value))
                for key, value in (changes or self.changes).items()
            ),
            key=(
                lambda x: field_order.index(x[0])
                if x[0] in field_order else 999
            )
        )
        return dict(result)

    @cached_property
    def translations(self) -> dict[str, Mapping[Any, str]]:
        LANGUAGES = {  # noqa: N806
            str(language.id): language.name
            for language in self.language_collection.query()
        }
        CERTIFICATES = {  # noqa: N806
            str(cert.id): cert.name
            for cert in self.certificate_collection.query()
        }
        BOOLS = {True: _('Yes'), False: _('No')}  # noqa: N806

        return {
            'admission': ADMISSIONS,
            'confirm_name_reveal': BOOLS,
            'education_as_interpreter': BOOLS,
            'expertise_interpreting_types': INTERPRETING_TYPES,
            'expertise_professional_guilds': PROFESSIONAL_GUILDS,
            'gender': GENDERS,
            'self_employed': BOOLS,
            'withholding_tax': BOOLS,
            'mother_tongues': LANGUAGES,
            'spoken_languages': LANGUAGES,
            'written_languages': LANGUAGES,
            'monitoring_languages': LANGUAGES,
            'certificates': CERTIFICATES
        }

    labels: ClassVar[Mapping[str, TranslationString]] = {
        'first_name': _('First name'),
        'last_name': _('Last name'),
        'pers_id': _('Personal ID'),
        'admission': _('Admission'),
        'withholding_tax': _('Withholding tax'),
        'self_employed': _('Self-employed'),
        'gender': _('Gender'),
        'date_of_birth': _('Date of birth'),
        'nationalities': _('Nationality(ies)'),
        'coordinates': _('Location'),
        'address': _('Street and house number'),
        'zip_code': _('Zip Code'),
        'city': _('City'),
        'drive_distance': _('Drive distance (km)'),
        'social_sec_number': _('Swiss social security number'),
        'bank_name': _('Bank name'),
        'bank_address': _('Bank address'),
        'account_owner': _('Account owner'),
        'iban': _('IBAN'),
        'email': _('Email'),
        'tel_mobile': _('Mobile Number'),
        'tel_private': _('Private Phone Number'),
        'tel_office': _('Office Phone Number'),
        'availability': _('Availability'),
        'operation_comments': _(
            'Comments on possible field of application'
        ),
        'confirm_name_reveal': _('Name revealing confirmation'),
        'date_of_application': _('Date of application'),
        'date_of_decision': _('Date of decision'),
        'mother_tongues': _('Mother tongues'),
        'spoken_languages': _('Spoken languages'),
        'written_languages': _('Written languages'),
        'monitoring_languages': _('Monitoring languages'),
        'profession': _('Learned profession'),
        'occupation': _('Current professional activity'),
        'expertise_professional_guilds': _(
            'Expertise by professional guild'
        ),
        'expertise_professional_guilds_other': _(
            'Expertise by professional guild: other'
        ),
        'expertise_interpreting_types': _(
            'Expertise by interpreting type'
        ),
        'proof_of_preconditions': _('Proof of preconditions'),
        'agency_references': _('Agency references'),
        'education_as_interpreter': _('Education as interpreter'),
        'certificates': _('Language Certificates'),
        'comments': _('Comments'),
    }

    def apply(self, items: Iterable[str]) -> None:
        assert self.ticket is not None
        self.ticket.handler_data['state'] = 'applied'
        for item in items:
            if (changes := self.changes.get(item, _missing)) is not _missing:
                if item in (
                    'mother_tongues', 'spoken_languages', 'written_languages',
                    'monitoring_languages'
                ):
                    changes = self.language_collection.by_ids(changes)
                if item == 'certificates':
                    changes = self.certificate_collection.by_ids(changes)

                setattr(self.target, item, changes)
