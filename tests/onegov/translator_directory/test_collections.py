from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from tests.onegov.translator_directory.shared import create_languages, \
    create_translator


def test_translator_collection(session):
    langs = create_languages(session)
    collection = TranslatorCollection(session)
    james = create_translator(session, email='james@memo.com', last_name='Z')

    translator = session.query(collection.model_class).one()
    assert translator == collection.by_id(translator.id)
    assert collection.query().all() == [translator]

    # Adds second translator
    bob = create_translator(session, email='bob@memo.com', last_name='X')

    # Test filter spoken language
    collection.spoken_langs = [langs[0].id]
    assert not collection.query().first()
    james.spoken_languages.append(langs[0])
    assert collection.query().count() == 1

    # Test filter with multiple spoken languages
    collection.spoken_langs = [langs[0].id, langs[1].id]
    assert not collection.query().first()

    # Add second language for james and test filter with two languages
    james.spoken_languages.append(langs[1])
    collection.spoken_langs = [langs[0].id, langs[1].id]
    assert collection.query().all() == [james]

    # Test filter with two languages
    bob.written_languages.append(langs[1])
    bob.written_languages.append(langs[2])
    bob.spoken_languages.append(langs[1])
    bob.spoken_languages.append(langs[2])
    collection.spoken_langs = [langs[2].id]
    collection.written_langs = collection.spoken_langs
    assert collection.query().all() == [bob]

    # Test filter with two languages spoken and written
    collection.written_langs = [langs[1].id, langs[2].id]
    collection.spoken_langs = collection.written_langs
    assert collection.query().all() == [bob]

    # Test ordering
    collection.spoken_langs = None
    collection.written_langs = None
    assert collection.order_by == 'last_name'
    assert collection.order_desc is False
    assert collection.query().all() == [bob, james]
    collection.order_desc = True
    assert collection.query().all() == [james, bob]


def test_collection_wrong_user_input(session):
    # Prevent wrong user input from going to the db query
    coll = TranslatorCollection(session, order_by='nothing', order_desc='hey')
    assert coll.order_desc is False
    assert coll.order_by == 'last_name'


def test_language_collection(session):
    coll = LanguageCollection(session)
    zulu = coll.add(name='Zulu')
    arabic = coll.add(name='Arabic')
    assert coll.query().all() == [arabic, zulu]
