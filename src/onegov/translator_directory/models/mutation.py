from cached_property import cached_property
from onegov.gis import Coordinates
from onegov.translator_directory import _
from onegov.translator_directory.constants import ADMISSIONS
from onegov.translator_directory.constants import GENDERS
from onegov.translator_directory.constants import INTERPRETING_TYPES
from onegov.translator_directory.constants import PROFESSIONAL_GUILDS


class TranslatorMutation:

    def __init__(self, session, target_id, ticket_id):
        self.session = session
        self.target_id = target_id
        self.ticket_id = ticket_id

    @cached_property
    def collection(self):
        from onegov.translator_directory.collections.translator import \
            TranslatorCollection
        return TranslatorCollection(self.session, user_role='admin')

    @cached_property
    def language_collection(self):
        from onegov.translator_directory.collections.language import \
            LanguageCollection
        return LanguageCollection(self.session)

    @cached_property
    def certificate_collection(self):
        from onegov.translator_directory.collections.certificate import \
            LanguageCertificateCollection
        return LanguageCertificateCollection(self.session)

    @cached_property
    def target(self):
        return self.collection.by_id(self.target_id)

    @cached_property
    def ticket(self):
        from onegov.ticket import TicketCollection
        return TicketCollection(self.session).by_id(self.ticket_id)

    @cached_property
    def changes(self):
        handler_data = self.ticket.handler_data['handler_data']
        result = handler_data.get('proposed_changes', {})
        result = {k: v for k, v in result.items() if hasattr(self.target, k)}
        return result

    def translated(self, request, changes=None):
        self.session = self.session or request.session

        def label(name):
            return request.translate(self.labels.get(name, name))

        def convert(name, value):
            if isinstance(value, Coordinates):
                return f'{value.lat}, {value.lon}'

            translations = self.translations.get(name)
            if translations:
                if isinstance(value, list):
                    return ', '.join([
                        request.translate(translations.get(v, v))
                        for v in value
                    ])
                return request.translate(translations.get(value, value))

            if isinstance(value, list):
                return ', '.join(value)

            return value

        return {
            key: (label(key), convert(key, value), value)
            for key, value in (changes or self.changes).items()
        }

    @cached_property
    def translations(self):
        LANGUAGES = {
            str(language.id): language.name
            for language in self.language_collection.query()
        }
        CERTIFICATES = {
            str(cert.id): cert.name
            for cert in self.certificate_collection.query()
        }
        BOOLS = {True: _('Yes'), False: _('No')}

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
            'certificates': CERTIFICATES
        }

    @cached_property
    def labels(self):
        return {
            'first_name': _('First name'),
            'last_name': _('Last name'),
            'pers_id': _('Personal ID'),
            'admission': _('Admission'),
            'withholding_tax': _('Withholding tax'),
            'self_employed': _('Self-employed'),
            'gender': _('Gender'),
            'date_of_birth': _('Date of birth'),
            'nationality': _('Nationality'),
            'coordinates': _("Location"),
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
            'mother_tongues': _('Mother tongues'),
            'spoken_languages': _('Spoken languages'),
            'written_languages': _('Written languages'),
            'expertise_professional_guilds': _(
                'Expertise by professional guild'
            ),
            'expertise_professional_guilds_other': _(
                'Expertise by professional guild: other'
            ),
            'expertise_interpreting_types': _(
                'Expertise by interpreting type'
            ),
            'agency_references': _('Agency references'),
            'education_as_interpreter': _('Education as interpreter'),
            'certificates': _('Language Certificates'),
        }

    def apply(self, items):
        self.ticket.handler_data['state'] = 'applied'
        for item in items:
            if item in self.changes:
                changes = self.changes[item]
                if item in (
                    'mother_tongues', 'spoken_languages', 'written_languages'
                ):
                    changes = self.language_collection.by_ids(changes)
                if item == 'certificates':
                    changes = self.certificate_collection.by_ids(changes)

                setattr(self.target, item, changes)
