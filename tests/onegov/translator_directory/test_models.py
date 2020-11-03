from onegov.gis import Coordinates
from onegov.translator_directory.collections.certificate import \
    LanguageCertificateCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from tests.onegov.translator_directory.shared import create_languages, \
    translator_data


def test_translator(session):
    langs = create_languages(session)
    translators = TranslatorCollection(session)
    translator = translators.add(
        **translator_data, mother_tongues=[langs[0]])

    assert translator.mother_tongues
    assert not translator.spoken_languages
    spoken = langs[0]
    translator.spoken_languages.append(spoken)
    assert translator.spoken_languages
    assert spoken.speakers == [translator]
    assert spoken.speakers_count == 1

    written = langs[1]
    translator.written_languages.append(written)
    assert written.writers == [translator]
    assert written.writers_count == 1
    assert translator.written_languages == [written]
    assert not translator.files

    cert = LanguageCertificateCollection(session).add(name='TestCert')
    translator.certificates.append(cert)
    session.flush()
    assert translator.certificates
    translator.drive_distance = 60.5
    session.flush()
