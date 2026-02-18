from __future__ import annotations

from datetime import date
from freezegun import freeze_time
from onegov.core.utils import Bunch
from onegov.gis import Coordinates
from onegov.translator_directory.collections.certificate import (
    LanguageCertificateCollection)
from onegov.translator_directory.collections.translator import (
    TranslatorCollection)
from onegov.translator_directory.models.ticket import AccreditationTicket
from onegov.translator_directory.models.ticket import (
    TranslatorMutationTicket)
from onegov.translator_directory.models.translator import Translator
from onegov.user import User
from onegov.user import UserCollection
from tests.onegov.translator_directory.shared import create_certificates
from tests.onegov.translator_directory.shared import create_languages
from tests.onegov.translator_directory.shared import create_translator
from tests.onegov.translator_directory.shared import translator_data


from typing import Any, TYPE_CHECKING
if TYPE_CHECKING:
    from sqlalchemy.orm import Session
    from .conftest import TestApp


def test_translator_model(translator_app: TestApp) -> None:
    session = translator_app.session()
    langs = create_languages(session)
    assert all((lang.deletable for lang in langs))

    translators = TranslatorCollection(translator_app)
    translator = translators.add(**translator_data, mother_tongues=[langs[0]])
    assert not translator.files

    assert translator.state == 'published'
    assert translator.mother_tongues
    assert not translator.spoken_languages
    assert not translator.written_languages
    assert not translator.monitoring_languages

    native = langs[0]
    assert native.mother_tongues == [translator]
    assert native.native_speakers_count == 1
    assert not native.deletable

    spoken = langs[1]
    translator.spoken_languages.append(spoken)
    assert translator.spoken_languages
    assert spoken.speakers == [translator]
    assert spoken.speakers_count == 1
    assert not spoken.deletable

    written = langs[2]
    translator.written_languages.append(written)
    assert written.writers == [translator]
    assert written.writers_count == 1
    assert translator.written_languages == [written]
    assert not written.deletable

    monitoring = langs[3]
    translator.monitoring_languages.append(monitoring)
    assert monitoring.monitors == [translator]
    assert monitoring.monitors_count == 1
    assert translator.monitoring_languages == [monitoring]
    assert not monitoring.deletable

    cert = LanguageCertificateCollection(session).add(name='TestCert')
    translator.certificates.append(cert)
    session.flush()
    assert translator.certificates
    translator.drive_distance = 60.5
    session.flush()

    # professional expertises
    assert translator.expertise_professional_guilds == tuple()
    assert translator.expertise_professional_guilds_other == tuple()
    assert translator.expertise_professional_guilds_all == tuple()

    translator.expertise_professional_guilds = ['economy', 'art_leisure']
    assert translator.expertise_professional_guilds_all == (
        'economy', 'art_leisure'
    )

    translator.expertise_professional_guilds_other = ['Psychologie']
    assert translator.expertise_professional_guilds_all == (
        'economy', 'art_leisure', 'Psychologie'
    )

    translator.expertise_professional_guilds = []
    assert translator.expertise_professional_guilds_all == ('Psychologie', )


def test_translator_user(session: Session) -> None:
    users = UserCollection(session)
    user_a = users.add(username='a@example.org', password='a', role='member')
    user_b = users.add(username='b@example.org', password='b', role='member')

    translator = Translator(
        first_name='Hugo',
        last_name='Benito',
    )
    session.add(translator)
    session.flush()

    if not TYPE_CHECKING:
        # we pretend this can't be true so we can't assert this at
        # type checking time otherwise everything becomes unreachable
        assert translator.user is None
    assert user_a.translator is None  # type: ignore[attr-defined]
    assert user_b.translator is None  # type: ignore[attr-defined]

    translator.email = 'a@example.org'
    session.flush()
    session.expire_all()
    assert translator.user == user_a
    assert user_a.translator == translator  # type: ignore[attr-defined]
    assert user_b.translator is None  # type: ignore[attr-defined]

    translator.email = 'b@example.org'
    session.flush()
    session.expire_all()
    assert translator.user == user_b
    assert user_a.translator is None  # type: ignore[attr-defined]
    assert user_b.translator == translator  # type: ignore[attr-defined]

    session.delete(user_b)
    session.flush()
    translator = session.query(Translator).one()
    user = session.query(User).one()
    assert translator.email == 'b@example.org'

    user.username = 'user@example.org'
    translator.email = 'user@example.org'
    session.flush()
    session.expire_all()
    assert translator.user == user
    assert user.translator == translator  # type: ignore[attr-defined]

    session.delete(translator)
    session.flush()
    assert session.query(User).one().username == 'user@example.org'


def test_translator_mutation(session: Session) -> None:
    languages = create_languages(session)
    certificates = create_certificates(session)

    translator = Translator(
        first_name='Hugo',
        last_name='Benito',
        confirm_name_reveal=True,
        mother_tongues=languages[:2],
        spoken_languages=languages[:2],
        certificates=certificates[:2],
        expertise_professional_guilds=('economy', 'social_science'),
        expertise_professional_guilds_other=('Psychologie',)
    )
    session.add(translator)
    session.flush()

    proposed_changes = {
        'first_name': 'First Name',
        'last_name': 'Last Name',
        'pers_id': 100,
        'admission': 'uncertified',
        'withholding_tax': True,
        'self_employed': False,
        'gender': 'M',
        'date_of_birth': '1970-01-01',
        'nationalities': 'nationalities',
        'coordinates': Coordinates(1, 2),
        'address': 'Street and house number',
        'zip_code': '8000',
        'city': 'City',
        'drive_distance': 10.02,
        'social_sec_number': '756.1234.5678.97',
        'bank_name': 'Bank name',
        'bank_address': 'Bank address',
        'account_owner': 'Account owner',
        'iban': 'CH0000000000000000000',
        'email': 'translator@example.org',
        'tel_mobile': '+11223334455',
        'tel_private': '+11223334466',
        'tel_office': '+11223334477',
        'availability': 'Availability',
        'operation_comments': 'Operation comments',
        'confirm_name_reveal': None,
        'date_of_application': date(2020, 1, 1),
        'date_of_decision': date(2020, 2, 2),
        'mother_tongues': [str(l.id) for l in languages[2:3]],
        'spoken_languages': [],
        'written_languages': [str(l.id) for l in languages[1:2]],
        'monitoring_languages': [str(l.id) for l in languages[0:1]],
        'profession': 'salesman',
        'occupation': 'lecturer',
        'expertise_professional_guilds': (
            'internation_relations',
            'law_insurance'
        ),
        'expertise_professional_guilds_other': [],
        'expertise_interpreting_types': [
            'simultaneous',
            'negotiation'
        ],
        'proof_of_preconditions': 'Proof of preconditions',
        'agency_references': 'Agency references',
        'education_as_interpreter': True,
        'certificates': [str(c.id) for c in certificates[2:3]],
        'comments': 'Comments',
        'extra': 'Extra'  # extra fields are ignored
    }

    ticket = TranslatorMutationTicket(
        number='TRN-1000-0000',
        title='TRN-1000-0000',
        group='TRN-1000-0000',
        handler_id='1',
        handler_data={
            'handler_data': {
                'id': str(translator.id),
                'submitter_email': 'editor@example.org',
                'submitter_message': 'Message',
                'proposed_changes': proposed_changes
            }
        }
    )
    session.add(ticket)
    session.flush()

    assert ticket.handler.translator == translator
    assert not ticket.handler.deleted
    assert ticket.handler.email == 'editor@example.org'
    assert ticket.handler.message == 'Message'
    assert ticket.handler.proposed_changes == proposed_changes
    assert ticket.handler.state is None
    assert ticket.handler.title == 'BENITO, Hugo'
    assert ticket.handler.subtitle == 'Mutation'
    assert ticket.handler.group == 'Translator'

    request: Any = Bunch(translate=lambda x: f'_{x}')
    mutation = ticket.handler.mutation
    assert mutation is not None
    proposed_changes.pop('extra')
    assert mutation.changes == proposed_changes
    assert mutation.target == translator
    assert mutation.ticket == ticket
    assert mutation.translated(request) == {
        'account_owner': (
            '_Account owner',
            'Account owner',
            'Account owner'
        ),
        'address': (
            '_Street and house number',
            'Street and house number',
            'Street and house number'
        ),
        'admission': ('_Admission', '_uncertified', 'uncertified'),
        'agency_references': (
            '_Agency references',
            'Agency references',
            'Agency references'
        ),
        'availability': ('_Availability', 'Availability', 'Availability'),
        'bank_address': ('_Bank address', 'Bank address', 'Bank address'),
        'bank_name': ('_Bank name', 'Bank name', 'Bank name'),
        'certificates': (
            '_Language Certificates',
            '_CCCC',
            [str(c.id) for c in certificates[2:3]]
        ),
        'city': ('_City', 'City', 'City'),
        'comments': ('_Comments', 'Comments', 'Comments'),
        'confirm_name_reveal': ('_Name revealing confirmation', '_None', None),
        'coordinates': (
            '_Location',
            '1, 2',
            Coordinates(1, 2)
        ),
        'date_of_application': (
            '_Date of application',
            date(2020, 1, 1),
            date(2020, 1, 1)
        ),
        'date_of_birth': ('_Date of birth', '1970-01-01', '1970-01-01'),
        'date_of_decision': (
            '_Date of decision',
            date(2020, 2, 2),
            date(2020, 2, 2)
        ),
        'drive_distance': ('_Drive distance (km)', 10.02, 10.02),
        'education_as_interpreter': (
            '_Education as interpreter',
            '_Yes',
            True
        ),
        'email': (
            '_Email',
            'translator@example.org',
            'translator@example.org'
        ),
        'expertise_interpreting_types': (
            '_Expertise by interpreting type',
            '_Simultaneous interpreting, _Negotiation interpreting',
            ['simultaneous', 'negotiation']
        ),
        'expertise_professional_guilds': (
            '_Expertise by professional guild',
            (
                '_International relations and organisations, '
                '_Law and insurance industry'
            ),
            ('internation_relations', 'law_insurance')
        ),
        'expertise_professional_guilds_other': (
            '_Expertise by professional guild: other',
            '',
            []
        ),
        'first_name': ('_First name', 'First Name', 'First Name'),
        'gender': ('_Gender', '_masculin', 'M'),
        'iban': ('_IBAN', 'CH0000000000000000000', 'CH0000000000000000000'),
        'last_name': ('_Last name', 'Last Name', 'Last Name'),
        'mother_tongues': (
            '_Mother tongues',
            '_Italian',
            [str(l.id) for l in languages[2:3]]
        ),
        'nationalities': ('_Nationality(ies)', 'nationalities',
                          'nationalities'),
        'operation_comments': (
            '_Comments on possible field of application',
            'Operation comments',
            'Operation comments'
        ),
        'pers_id': ('_Personal ID', 100, 100),
        'proof_of_preconditions': (
            '_Proof of preconditions',
            'Proof of preconditions',
            'Proof of preconditions'
        ),
        'self_employed': ('_Self-employed', '_No', False),
        'social_sec_number': (
            '_Swiss social security number',
            '756.1234.5678.97',
            '756.1234.5678.97'
        ),
        'spoken_languages': ('_Spoken languages', '', []),
        'tel_mobile': ('_Mobile Number', '+11223334455', '+11223334455'),
        'tel_office': ('_Office Phone Number', '+11223334477', '+11223334477'),
        'tel_private': (
            '_Private Phone Number',
            '+11223334466',
            '+11223334466'
        ),
        'withholding_tax': ('_Withholding tax', '_Yes', True),
        'written_languages': (
            '_Written languages',
            '_French',
            [str(l.id) for l in languages[1:2]]
        ),
        'monitoring_languages': (
            '_Monitoring languages',
            '_German',
            [str(l.id) for l in languages[0:1]]
        ),
        'zip_code': ('_Zip Code', '8000', '8000'),
        'profession': ('_Learned profession', 'salesman', 'salesman'),
        'occupation': (
            '_Current professional activity', 'lecturer', 'lecturer'
        )
    }

    changes = set(mutation.changes)
    changes.remove('first_name')
    changes.add('extra')
    mutation.apply(changes)
    session.flush()
    session.expire_all()
    assert ticket.handler_data['state'] == 'applied'
    assert translator.first_name == 'Hugo'
    assert translator.last_name == 'Last Name'
    assert translator.pers_id == 100
    assert translator.admission == 'uncertified'
    assert translator.withholding_tax is True
    assert translator.self_employed is False
    assert translator.gender == 'M'
    assert translator.date_of_birth == date(1970, 1, 1)
    assert translator.nationalities == 'nationalities'  # type: ignore[comparison-overlap]
    assert translator.coordinates == Coordinates(1, 2)
    assert translator.address == 'Street and house number'
    assert translator.zip_code == '8000'
    assert translator.city == 'City'
    assert translator.drive_distance == 10.02
    assert translator.social_sec_number == '756.1234.5678.97'
    assert translator.bank_name == 'Bank name'
    assert translator.bank_address == 'Bank address'
    assert translator.account_owner == 'Account owner'
    assert translator.iban == 'CH0000000000000000000'
    assert translator.email == 'translator@example.org'
    assert translator.tel_mobile == '+11223334455'
    assert translator.tel_private == '+11223334466'
    assert translator.tel_office == '+11223334477'
    assert translator.availability == 'Availability'
    assert translator.operation_comments == 'Operation comments'
    assert translator.confirm_name_reveal is None
    assert translator.date_of_application == date(2020, 1, 1)
    assert translator.date_of_decision == date(2020, 2, 2)
    assert translator.mother_tongues == languages[2:3]
    assert translator.spoken_languages == []
    assert translator.written_languages == languages[1:2]
    assert translator.monitoring_languages == languages[0:1]
    assert translator.profession == 'salesman'
    assert translator.occupation == 'lecturer'
    assert translator.expertise_professional_guilds == [
        'internation_relations',
        'law_insurance'
    ]
    assert translator.expertise_professional_guilds_other == []
    assert translator.expertise_interpreting_types == [
        'simultaneous',
        'negotiation'
    ]
    assert translator.proof_of_preconditions == 'Proof of preconditions'
    assert translator.agency_references == 'Agency references'
    assert translator.education_as_interpreter is True
    assert translator.certificates == certificates[2:3]
    assert translator.comments == 'Comments'

    mutation.apply(list(mutation.changes))
    session.flush()
    session.expire_all()
    assert translator.first_name == 'First Name'
    assert translator.last_name == 'Last Name'


def test_accreditation(translator_app: TestApp) -> None:
    session = translator_app.session()
    translator = create_translator(translator_app, state='proposed')
    ticket = AccreditationTicket(
        number='AKK-1000-0000',
        title='AKK-1000-0000',
        group='AKK-1000-0000',
        handler_id='1',
        handler_data={
            'handler_data': {
                'id': str(translator.id),
                'submitter_email': 'translator@example.org',
            }
        }
    )
    session.add(ticket)
    session.flush()
    accreditation = ticket.handler.accreditation
    assert accreditation is not None

    assert translator.state == 'proposed'
    assert ticket.handler.translator == translator
    assert not ticket.handler.deleted
    assert ticket.handler.email == 'translator@example.org'
    assert ticket.handler.state is None
    assert ticket.handler.title == 'BENITO, Hugo'
    assert ticket.handler.subtitle == 'Request Accreditation'
    assert ticket.handler.group == 'Accreditation'
    assert accreditation.target == translator
    assert accreditation.ticket == ticket

    with freeze_time('2026-01-01') as today:
        accreditation.grant()
        # undo mypy narrowing
        translator = translator
        assert ticket.handler.state == 'granted'
        assert translator.state == 'published'
        assert translator.date_of_decision == today().date()
        assert session.query(Translator).count() == 1

    with freeze_time('2025-01-01') as today:
        accreditation.refuse()
        assert ticket.handler.state == 'refused'
        assert session.query(Translator).count() == 0
        assert ticket.handler.deleted
