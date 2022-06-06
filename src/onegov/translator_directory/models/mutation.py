from cached_property import cached_property
from onegov.agency import _


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

    @property
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
            'mother_tongues_ids': _('Mother tongues'),
            'spoken_languages_ids': _('Spoken languages'),
            'written_languages_ids': _('Written languages'),
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
            'certificates_ids': _('Language Certificates'),
        }

    def apply(self, items):
        self.ticket.handler_data['state'] = 'applied'
        for item in items:
            if item in self.changes:
                setattr(self.target, item, self.changes[item])
