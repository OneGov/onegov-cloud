from cgi import FieldStorage
from datetime import date
from io import BytesIO
from onegov.core.utils import Bunch
from onegov.gis import Coordinates
from onegov.pdf import Pdf
from onegov.translator_directory.forms.accreditation import \
    RequestAccreditationForm
from onegov.translator_directory.forms.mutation import TranslatorMutationForm
from onegov.translator_directory.models.translator import Translator
from tests.onegov.translator_directory.shared import create_certificates
from tests.onegov.translator_directory.shared import create_languages
from tests.onegov.translator_directory.shared import create_translator
from tests.shared.utils import encode_map_value


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


def create_file(filename):
    file = BytesIO()
    pdf = Pdf(file)
    pdf.init_report()
    pdf.p(filename)
    pdf.generate()
    file.seek(0)

    result = FieldStorage()
    result.type = 'application/pdf'
    result.filename = filename
    result.file = file
    return result


def test_translator_mutation_form(translator_app):
    session = translator_app.session()
    certificates = create_certificates(session)
    languages = create_languages(session)

    translator = create_translator(
        translator_app,
        admission='uncertified',
        comments='Some other comment',
        confirm_name_reveal=True,
        date_of_application=date(2000, 1, 1),
        date_of_birth=date(1970, 1, 1),
        date_of_decision=date(2001, 1, 1),
        drive_distance=1.1,
        expertise_professional_guilds=['economy', 'military'],
        expertise_professional_guilds_other=['Psychology'],
        expertise_interpreting_types=['whisper', 'negotiation'],
        gender='M',
        iban='CH9300762011623852957',
        operation_comments='Some comment',
        tel_private='041 444 44 45',
        nationalities=['CH'],
        tel_mobile='079 123 45 67',
        social_sec_number='756.1234.4568.95',
    )
    translator.certificates = certificates[0:2]
    translator.mother_tongues = languages[0:2]
    translator.spoken_languages = languages[1:3]
    translator.written_languages = languages[2:4]
    translator.monitoring_languages = languages[3:4]
    translator.coordinates = Coordinates(1, 2, 12)

    request = Bunch(
        app=translator_app,
        session=session,
        locale='de_CH',
        is_manager=True,
        is_admin=True,
        is_editor=False,
        is_member=False,
        is_translator=False,
        include=lambda x: x,
        translate=lambda x: f'_{x}',
        url=''
    )

    form = TranslatorMutationForm()
    form.model = translator
    form.request = request
    form.on_request()

    # Test long descriptions
    assert form.first_name.long_description == 'Hugo'
    assert form.last_name.long_description == 'Benito'
    assert form.pers_id.long_description == '1234'
    assert form.admission.long_description == '_uncertified'
    assert form.withholding_tax.long_description == '_No'
    assert form.self_employed.long_description == '_No'
    assert form.gender.long_description == '_masculin'
    assert form.date_of_birth.long_description == '01.01.1970'
    assert form.nationalities.long_description == '_Schweiz'
    assert form.address.long_description == 'Downing Street 5'
    assert form.zip_code.long_description == '4000'
    assert form.city.long_description == 'Luzern'
    assert form.drive_distance.long_description == '1.1'
    assert form.social_sec_number.long_description == '756.1234.4568.95'
    assert form.bank_name.long_description == 'R-BS'
    assert form.bank_address.long_description == 'Bullstreet 5'
    assert form.account_owner.long_description == 'Hugo Benito'
    assert form.iban.long_description == 'CH9300762011623852957'
    assert form.email.long_description == 'hugo@benito.com'
    assert form.tel_mobile.long_description == '079 123 45 67'
    assert form.tel_private.long_description == '041 444 44 45'
    assert form.tel_office.long_description == '041 444 44 44'
    assert form.availability.long_description == 'always'
    assert form.operation_comments.long_description == 'Some comment'
    assert form.confirm_name_reveal.long_description == '_Yes'
    assert form.date_of_application.long_description == '01.01.2000'
    assert form.date_of_decision.long_description == '01.01.2001'
    assert form.mother_tongues.long_description == '_German, _French'
    assert form.spoken_languages.long_description == '_French, _Italian'
    assert form.written_languages.long_description == '_Italian, _Arabic'
    assert form.monitoring_languages.long_description == '_Arabic'
    assert form.profession.long_description == 'craftsman'
    assert form.occupation.long_description == 'baker'
    assert form.expertise_professional_guilds.long_description == \
        '_Economy, _Military'
    assert form.expertise_professional_guilds_other.long_description == \
        'Psychology'
    assert form.expertise_interpreting_types.long_description == \
        '_Whisper interpreting, _Negotiation interpreting'
    assert form.proof_of_preconditions.long_description == 'all okay'
    assert form.agency_references.long_description == 'Some ref'
    assert form.education_as_interpreter.long_description == '_No'
    assert form.certificates.long_description == '_AAAA, _BBBB'
    assert form.comments.long_description == 'Some other comment'

    # Test inserting of no choice
    assert form.admission.choices[0] == ('', '_')
    assert form.withholding_tax.choices[0] == ('', '_')
    assert form.self_employed.choices[0] == ('', '_')
    assert form.gender.choices[0] == ('', '_')
    assert form.confirm_name_reveal.choices[0] == ('', '_')
    assert form.mother_tongues.choices[0] == ('', '_')
    assert form.spoken_languages.choices[0] == ('', '_')
    assert form.written_languages.choices[0] == ('', '_')
    assert form.monitoring_languages.choices[0] == ('', '_')
    assert form.expertise_professional_guilds.choices[0] == ('', '_')
    assert form.expertise_interpreting_types.choices[0] == ('', '_')
    assert form.education_as_interpreter.choices[0] == ('', '_')
    assert form.certificates.choices[0] == ('', '_')

    # Test translating choices
    assert form.admission.choices[1][1] == '_uncertified'
    assert form.withholding_tax.choices[1][1] == '_Yes'
    assert form.self_employed.choices[1][1] == '_Yes'
    assert form.gender.choices[1][1] == '_masculin'
    assert form.confirm_name_reveal.choices[1][1] == '_Yes'
    assert form.mother_tongues.choices[1][1] == '_Arabic'
    assert form.spoken_languages.choices[1][1] == '_Arabic'
    assert form.written_languages.choices[1][1] == '_Arabic'
    assert form.monitoring_languages.choices[1][1] == '_Arabic'
    assert form.expertise_professional_guilds.choices[1][1] == \
        '_Nutrition and agriculture'
    assert form.expertise_interpreting_types.choices[1][1] == \
        '_Simultaneous interpreting'
    assert form.education_as_interpreter.choices[1][1] == '_Yes'
    assert form.certificates.choices[1][1] == '_AAAA'

    # Test removing fields by role
    form = TranslatorMutationForm()
    form.model = translator
    form.request = request
    form.request.is_admin = False
    form.request.is_translator = True
    form.on_request()
    assert len(form._fields) == 55
    assert len(form.proposal_fields) == 43

    form = TranslatorMutationForm()
    form.model = translator
    form.request = request
    form.request.is_translator = False
    form.request.is_editor = True
    form.on_request()
    assert len(form._fields) == 44
    assert len(form.proposal_fields) == 32
    assert form.operation_comments is None
    assert form.confirm_name_reveal is None
    assert form.date_of_application is None
    assert form.date_of_decision is None
    assert form.proof_of_preconditions is None
    assert form.agency_references is None
    assert form.education_as_interpreter is None
    assert form.certificates is None
    assert form.comments is None

    form = TranslatorMutationForm()
    form.model = translator
    form.request = request
    form.request.is_editor = False
    form.request.is_member = True
    form.on_request()
    assert len(form._fields) == 39
    assert len(form.proposal_fields) == 27
    assert form.operation_comments is None
    assert form.confirm_name_reveal is None
    assert form.date_of_application is None
    assert form.date_of_decision is None
    assert form.proof_of_preconditions is None
    assert form.agency_references is None
    assert form.education_as_interpreter is None
    assert form.certificates is None
    assert form.comments is None
    assert form.social_sec_number is None
    assert form.bank_name is None
    assert form.bank_address is None
    assert form.account_owner is None
    assert form.iban is None

    # Test proposed changes
    form = TranslatorMutationForm(DummyPostData({}))
    assert not form.validate()
    assert form.errors == {
        'submitter_message': [
            'Please enter a message, suggest changes, or upload ' 'documents.'
        ]
    }
    assert form.proposed_changes == {}

    form = TranslatorMutationForm(DummyPostData({
        'submitter_message': 'Please delete me!'
    }))
    assert form.validate()
    assert form.proposed_changes == {}

    form = TranslatorMutationForm(DummyPostData({
        'first_name': 'Hugo',
        'last_name': 'Benito',
        'pers_id': '1234',
        'admission': 'uncertified',
        'withholding_tax': False,
        'self_employed': False,
        'gender': 'M',
        'date_of_birth': '1970-01-01',
        'nationalities': ['CH'],
        'coordinates': encode_map_value({'lat': 1, 'lon': 2, 'zoom': 12}),
        'address': 'Downing Street 5',
        'zip_code': '4000',
        'city': 'Luzern',
        'drive_distance': 1.1,
        'social_sec_number': '756.1234.4568.95',
        'bank_name': 'R-BS',
        'bank_address': 'Bullstreet 5',
        'account_owner': 'Hugo Benito',
        'iban': 'CH9300762011623852957',
        'tel_mobile': '079 123 45 67',
        'tel_private': '041 444 44 45',
        'tel_office': '041 444 44 44',
        'availability': 'always',
        'operation_comments': 'Some comment',
        'confirm_name_reveal': True,
        'date_of_application': '2000-01-01',
        'date_of_decision': '2001-01-01',
        'mother_tongues': [str(x.id) for x in languages[0:2]],
        'spoken_languages': [str(x.id) for x in languages[1:3]],
        'written_languages': [str(x.id) for x in languages[2:4]],
        'monitoring_languages': [str(x.id) for x in languages[3:4]],
        'profession': 'craftsman',
        'occupation': 'baker',
        'expertise_professional_guilds': ['economy', 'military'],
        'expertise_professional_guilds_other': ['Psychology'],
        'expertise_interpreting_types': ['whisper', 'negotiation'],
        'proof_of_preconditions': 'all okay',
        'agency_references': 'Some ref',
        'education_as_interpreter': False,
        'certificates': [str(x.id) for x in certificates[0:2]],
        'comments': 'Some other comment',
    }))
    form.model = translator
    form.request = request
    form.request.is_admin = True
    form.on_request()
    assert form.proposed_changes == {}
    assert not form.validate()
    assert form.errors == {
        'submitter_message': [
            'Please enter a message, suggest changes, or upload ' 'documents.'
        ]
    }
    assert form.proposed_changes == {}

    form.model = Translator()
    form.model.content = {}
    form.model.coordinates = Coordinates()
    assert not form.validate()
    assert form.errors == {
        'coordinates': [
            'Home location is not configured. Please complete location '
            'settings first'
        ]
    }
    assert form.proposed_changes == {
        'first_name': 'Hugo',
        'last_name': 'Benito',
        'pers_id': 1234,
        'admission': 'uncertified',
        'withholding_tax': False,
        'self_employed': False,
        'gender': 'M',
        'date_of_birth': date(1970, 1, 1),
        'nationalities': ['CH'],
        'coordinates': Coordinates(1, 2, 12),
        'address': 'Downing Street 5',
        'zip_code': '4000',
        'city': 'Luzern',
        'drive_distance': 1.1,
        'social_sec_number': '756.1234.4568.95',
        'bank_name': 'R-BS',
        'bank_address': 'Bullstreet 5',
        'account_owner': 'Hugo Benito',
        'iban': 'CH9300762011623852957',
        'tel_mobile': '079 123 45 67',
        'tel_private': '041 444 44 45',
        'tel_office': '041 444 44 44',
        'availability': 'always',
        'operation_comments': 'Some comment',
        'confirm_name_reveal': True,
        'date_of_application': date(2000, 1, 1),
        'date_of_decision': date(2001, 1, 1),
        'mother_tongues': [str(x.id) for x in languages[0:2]],
        'spoken_languages': [str(x.id) for x in languages[1:3]],
        'written_languages': [str(x.id) for x in languages[2:4]],
        'monitoring_languages': [str(x.id) for x in languages[3:4]],
        'profession': 'craftsman',
        'occupation': 'baker',
        'expertise_professional_guilds': ['economy', 'military'],
        'expertise_professional_guilds_other': ['Psychology'],
        'expertise_interpreting_types': ['whisper', 'negotiation'],
        'proof_of_preconditions': 'all okay',
        'agency_references': 'Some ref',
        'education_as_interpreter': False,
        'certificates': [str(x.id) for x in certificates[0:2]],
        'comments': 'Some other comment',
    }

    # Test document uploads
    form = TranslatorMutationForm(
        DummyPostData(
            {
                'uploaded_certificates': create_file('certificate.pdf'),
                'passport': create_file('passport.pdf'),
            }
        )
    )
    form.request = request
    assert form.validate()
    files = form.get_files()
    assert len(files) == 2
    assert files[0].note == 'Mutationsmeldung'
    assert files[1].note == 'Mutationsmeldung'

    # Test document upload with empty data
    form = TranslatorMutationForm(DummyPostData({}))
    form.request = request
    files = form.get_files()
    assert files == []

    # Test valid submission with only documents (no message or changes)
    form = TranslatorMutationForm(
        DummyPostData({'resume': create_file('resume.pdf')})
    )
    form.request = request
    assert form.validate()
    assert form.proposed_changes == {}
    files = form.get_files()
    assert len(files) == 1


def test_accreditation_form(translator_app):
    session = translator_app.session()
    languages = create_languages(session)
    create_translator(translator_app)

    request = Bunch(
        app=translator_app,
        session=session,
        include=lambda x: x,
        translate=lambda x: f'_{x}',
        locale='de_CH',
    )

    # Test translations of choices
    form = RequestAccreditationForm()
    form.request = request
    form.on_request()

    assert '_neutral' in dict(form.gender.choices).values()
    assert 'German' in dict(form.mother_tongues_ids.choices).values()
    assert 'German' in dict(form.spoken_languages_ids.choices).values()
    assert 'German' in dict(form.written_languages_ids.choices).values()
    assert 'German' in dict(form.monitoring_languages_ids.choices).values()
    assert '_Military' in \
        dict(form.expertise_professional_guilds.choices).values()
    assert '_Negotiation interpreting' in \
        dict(form.expertise_interpreting_types.choices).values()

    # Test validation
    form = RequestAccreditationForm(DummyPostData({
        'email': 'hugo@benito.com',
        'zip_code': '12',
        'self_employed': False
    }))
    form.request = request
    form.on_request()
    assert not form.validate()
    assert form.errors['confirm_submission'] == [
        'Please confirm the correctness of the above data.'
    ]
    assert form.errors['zip_code'] == [
        'Zip code must consist of 4 digits'
    ]
    assert form.errors['email'] == [
        'A translator with this email already exists'
    ]
    assert form.errors['tel_mobile'] == [
        'This field is required.'
    ]
    assert 'confirmation_compensation_office' not in form.errors

    # ... extra document required if self employed
    form = RequestAccreditationForm(DummyPostData({'self_employed': True}))
    form.request = request
    form.on_request()
    assert not form.validate()
    assert form.errors['confirmation_compensation_office'] == [
        'This field is required.'
    ]

    # Test get data
    data = {
        'last_name': 'Benito',
        'first_name': 'Hugo',
        'gender': 'M',
        'date_of_birth': '1970-01-01',
        'hometown': 'Zug',
        'nationalities': ['CH'],
        'marital_status': 'verheiratet',
        'coordinates': encode_map_value({'lat': 1, 'lon': 2, 'zoom': 12}),
        'address': 'Downing Street 5',
        'zip_code': '4000',
        'city': 'Luzern',
        'drive_distance': 1.1,
        'withholding_tax': False,
        'self_employed': False,
        'social_sec_number': '756.1234.4568.90',
        'bank_name': 'R-BS',
        'bank_address': 'Bullstreet 5',
        'account_owner': 'Hugo Benito',
        'iban': 'CH9300762011623852957',
        'email': 'hugo.benito@translators.com',
        'tel_private': '041 444 44 45',
        'tel_office': '041 444 44 44',
        'tel_mobile': '079 000 00 00',
        'availability': '24h',
        'confirm_name_reveal': True,
        'profession': 'Baker',
        'occupation': 'Reporter',
        'education_as_interpreter': False,
        'mother_tongues_ids': [str(languages[0].id)],
        'spoken_languages_ids': [str(languages[1].id)],
        'written_languages_ids': [str(languages[2].id)],
        'monitoring_languages_ids': [str(languages[3].id)],
        'expertise_professional_guilds': ['economy', 'military'],
        'expertise_professional_guilds_other': ['Psychology'],
        'expertise_interpreting_types': ['whisper', 'negotiation'],
        'agency_references': 'Some ref',
        'admission_course_completed': False,
        'admission_course_agreement': True,
        'declaration_of_authorization': create_file('1.pdf'),
        'letter_of_motivation': create_file('2.pdf'),
        'resume': create_file('3.pdf'),
        'certificates': create_file('4.pdf'),
        'social_security_card': create_file('5.pdf'),
        'passport': create_file('6.pdf'),
        'passport_photo': create_file('7.pdf'),
        'debt_collection_register_extract': create_file('8.pdf'),
        'criminal_register_extract': create_file('9.pdf'),
        'certificate_of_capability': create_file('A.pdf'),
        'remarks': 'Some remarks',
        'confirm_submission': True
    }
    form = RequestAccreditationForm(DummyPostData(data))
    form.request = request
    form.on_request()
    assert not form.validate()
    assert form.errors == {
        'coordinates': [
            'Home location is not configured. Please complete location '
            'settings first'
        ]
    }

    assert form.get_translator_data() == {
        'state': 'proposed',
        'last_name': 'Benito',
        'first_name': 'Hugo',
        'gender': 'M',
        'date_of_birth': date(1970, 1, 1),
        'nationalities': ['CH'],
        'coordinates': Coordinates(1, 2, 12),
        'address': 'Downing Street 5',
        'zip_code': '4000',
        'city': 'Luzern',
        'hometown': 'Zug',
        'drive_distance': 1.1,
        'withholding_tax': False,
        'self_employed': False,
        'social_sec_number': '756.1234.4568.90',
        'bank_name': 'R-BS',
        'bank_address': 'Bullstreet 5',
        'account_owner': 'Hugo Benito',
        'iban': 'CH9300762011623852957',
        'email': 'hugo.benito@translators.com',
        'tel_private': '041 444 44 45',
        'tel_office': '041 444 44 44',
        'tel_mobile': '079 000 00 00',
        'availability': '24h',
        'confirm_name_reveal': True,
        'education_as_interpreter': False,
        'mother_tongues': [languages[0]],
        'spoken_languages': [languages[1]],
        'written_languages': [languages[2]],
        'monitoring_languages': [languages[3]],
        'profession': 'Baker',
        'occupation': 'Reporter',
        'expertise_professional_guilds': ['economy', 'military'],
        'expertise_professional_guilds_other': ['Psychology'],
        'expertise_interpreting_types': ['whisper', 'negotiation'],
        'agency_references': 'Some ref',
        'admission': 'uncertified',
        'date_of_application': date.today()
    }
    files = form.get_files()
    files = {(file.note, file.name, file.reference.filename) for file in files}
    assert files == {
        ('Antrag', '_Signed declaration of authorization.pdf', '1.pdf'),
        ('Antrag', '_Short letter of motivation.pdf', '2.pdf'),
        ('Antrag', '_Resume.pdf', '3.pdf'),
        ('Diplome und Zertifikate', '_Certificates.pdf', '4.pdf'),
        ('Antrag', '_Social security card.pdf', '5.pdf'),
        (
            'Antrag',
            '_Identity card, passport or foreigner identity card.pdf',
            '6.pdf'
        ),
        ('Antrag', '_Current passport photo.pdf', '7.pdf'),
        (
            'Abklärungen',
            '_Current extract from the debt collection register.pdf',
            '8.pdf'
        ),
        (
            'Abklärungen',
            '_Current extract from the Central Criminal Register.pdf',
            '9.pdf'
        ),
        ('Abklärungen', '_Certificate of Capability.pdf', 'A.pdf'),
    }
    assert form.get_ticket_data() == {
        'marital_status': 'verheiratet',
        'admission_course_completed': False,
        'admission_course_agreement': True,
        'remarks': 'Some remarks',
    }

    # ... extra document required if self employed
    data['self_employed'] = True
    data['confirmation_compensation_office'] = create_file('B.pdf')
    form = RequestAccreditationForm(DummyPostData(data))
    form.request = request
    form.on_request()
    assert not form.validate()
    assert form.errors == {
        'coordinates': [
            'Home location is not configured. Please complete location '
            'settings first'
        ]
    }

    files = form.get_files()
    files = {(file.note, file.name, file.reference.filename) for file in files}
    assert files == {
        ('Antrag', '_Signed declaration of authorization.pdf', '1.pdf'),
        ('Antrag', '_Short letter of motivation.pdf', '2.pdf'),
        ('Antrag', '_Resume.pdf', '3.pdf'),
        ('Diplome und Zertifikate', '_Certificates.pdf', '4.pdf'),
        ('Antrag', '_Social security card.pdf', '5.pdf'),
        (
            'Antrag',
            '_Identity card, passport or foreigner identity card.pdf',
            '6.pdf'
        ),
        ('Antrag', '_Current passport photo.pdf', '7.pdf'),
        (
            'Abklärungen',
            '_Current extract from the debt collection register.pdf',
            '8.pdf'
        ),
        (
            'Abklärungen',
            '_Current extract from the Central Criminal Register.pdf',
            '9.pdf'
        ),
        ('Abklärungen', '_Certificate of Capability.pdf', 'A.pdf'),
        (
            'Abklärungen',
            '_Confirmation from the compensation office regarding '
            'self-employment.pdf',
            'B.pdf'
        )
    }
