from onegov.gis import Coordinates
from onegov.translator_directory.collections.certificate import \
    LanguageCertificateCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.models.translator import Translator
from tests.onegov.translator_directory.shared import create_languages, \
    translator_data
from onegov.user import User, UserCollection


def test_translator(session):
    langs = create_languages(session)
    assert all((lang.deletable for lang in langs))

    translators = TranslatorCollection(session)
    translator = translators.add(**translator_data, mother_tongues=[langs[0]])

    assert translator.mother_tongues
    assert not translator.spoken_languages
    spoken = langs[0]
    translator.spoken_languages.append(spoken)
    assert translator.spoken_languages
    assert spoken.speakers == [translator]
    assert spoken.speakers_count == 1
    assert not spoken.deletable

    written = langs[1]
    translator.written_languages.append(written)
    assert written.writers == [translator]
    assert written.writers_count == 1
    assert translator.written_languages == [written]
    assert not translator.files
    assert not written.deletable

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


def test_translator_user(session):
    users = UserCollection(session)
    user_a = users.add(username='a@example.org', password='a', role='member')
    user_b = users.add(username='b@example.org', password='b', role='member')

    translator = Translator(
        first_name='Hugo',
        last_name='Benito',
    )
    session.add(translator)
    session.flush()

    assert translator.user is None
    assert user_a.translator is None
    assert user_b.translator is None

    translator.email = 'a@example.org'
    session.flush()
    session.expire_all()
    assert translator.user == user_a
    assert user_a.translator == translator
    assert user_b.translator is None

    translator.email = 'b@example.org'
    session.flush()
    session.expire_all()
    assert translator.user == user_b
    assert user_a.translator is None
    assert user_b.translator == translator

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
    assert user.translator == translator

    session.delete(translator)
    session.flush()
    assert session.query(User).one().username == 'user@example.org'


def test_translator_collection(session):
    translators = TranslatorCollection(session)
    trs = translators.add(
        **translator_data,
        coordinates=Coordinates()
    )
    # somehow, the instance has to be created in order to have deferred content
    # def add() would not have been overwritten
    assert trs.coordinates == Coordinates()
