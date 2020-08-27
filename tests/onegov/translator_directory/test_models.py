from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from tests.onegov.translator_directory.shared import create_languages, \
    translator_data


def test_translator(session):
    langs = create_languages(session)
    translators = TranslatorCollection(session)
    translator = translators.add(
        **translator_data, mother_tongue_id=langs[0].id)

    assert translator.mother_tongue
    assert not translator.spoken_languages
    spoken = langs[0]
    translator.spoken_languages.append(spoken)
    assert translator.spoken_languages
    assert spoken.speakers == [translator]

    written = langs[1]
    translator.written_languages.append(written)
    assert written.writers == [translator]
    assert translator.written_languages == [written]
    assert not translator.certificates
    assert not translator.applications
