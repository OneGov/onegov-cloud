from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.constants import INTERPRETING_TYPES, \
    PROFESSIONAL_GUILDS
from tests.onegov.translator_directory.shared import create_languages, \
    create_translator


def test_translator_search(session):
    interpreting_types = list(INTERPRETING_TYPES.keys())
    guild_types = list(PROFESSIONAL_GUILDS.keys())
    seba = create_translator(
        session,
        email='sm@mh.ch',
        first_name='Sebastian Hans',
        last_name='Meier Hugentobler',
        expertise_interpreting_types=[],
        expertise_professional_guilds=guild_types[0:3],
        expertise_professional_guilds_other=['Psychologie', 'Religion']
    )

    mary = create_translator(
        session,
        email='mary@t.ch',
        first_name='Mary Astiana',
        last_name='Sitkova Lavrova',
        expertise_interpreting_types=interpreting_types[0:1],
        expertise_professional_guilds=[],
        expertise_professional_guilds_other=['Geologie']
    )

    translators = TranslatorCollection(session)

    # term
    translators.search = 'Lavrov'
    assert translators.query().one().last_name == 'Sitkova Lavrova'

    translators.search = 'mari sitkova'
    assert translators.query().one().last_name == 'Sitkova Lavrova'

    translators.search = 'Sebastian astian'
    assert translators.query().all() == [seba, mary]

    translators.search = 'astian'
    assert translators.query().all() == [seba, mary]

    # interpreting types
    translators.interpret_types = [interpreting_types[0]]
    assert translators.query().all() == [mary]
    translators.interpret_types.append(interpreting_types[1])
    assert translators.query().all() == []

    # professional expertise
    assert translators.available_additional_professional_guilds == [
        'Geologie', 'Psychologie', 'Religion'
    ]

    translators.interpret_types = []
    translators.guilds = guild_types[0:2]
    assert translators.query().all() == [seba]

    translators.search = ''
    translators.guilds = [guild_types[0], 'Psychologie', 'Religion']
    assert translators.query().all() == [seba]

    translators.search = ''
    translators.guilds = ['Geologie']
    assert translators.query().all() == [mary]


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
