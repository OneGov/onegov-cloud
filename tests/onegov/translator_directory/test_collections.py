from onegov.gis import Coordinates
from onegov.translator_directory.collections.language import LanguageCollection
from onegov.translator_directory.collections.translator import \
    TranslatorCollection
from onegov.translator_directory.constants import INTERPRETING_TYPES, \
    PROFESSIONAL_GUILDS
from onegov.user import UserCollection
from tests.onegov.translator_directory.shared import create_languages, \
    create_translator, translator_data


def test_translator_collection_search(translator_app):
    interpreting_types = list(INTERPRETING_TYPES.keys())
    guild_types = list(PROFESSIONAL_GUILDS.keys())
    seba = create_translator(
        translator_app,
        email='sm@mh.ch',
        first_name='Sebastian Hans',
        last_name='Meier Hugentobler',
        expertise_interpreting_types=[],
        expertise_professional_guilds=guild_types[0:3],
        expertise_professional_guilds_other=['Psychologie', 'Religion']
    )

    mary = create_translator(
        translator_app,
        email='mary@t.ch',
        first_name='Mary Astiana',
        last_name='Sitkova Lavrova',
        expertise_interpreting_types=interpreting_types[0:1],
        expertise_professional_guilds=[],
        expertise_professional_guilds_other=['Geologie']
    )

    translators = TranslatorCollection(translator_app)

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

    # state
    seba.state = 'proposed'
    translators.guilds = []
    translators.state = 'proposed'
    assert translators.query().all() == [seba]


def test_translator_collection(translator_app):
    session = translator_app.session()
    langs = create_languages(session)
    collection = TranslatorCollection(translator_app)
    james = create_translator(
        translator_app, email='james@memo.com', last_name='Z', gender='M'
    )

    translator = session.query(collection.model_class).one()
    assert translator == collection.by_id(translator.id)
    assert collection.query().all() == [translator]

    # Adds second translator
    bob = create_translator(
        translator_app, email='bob@memo.com', last_name='X', gender='M'
    )

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

    # Test search by admission
    collection.admissions = ['certified']
    james.admission = 'certified'
    bob.admission = 'in_progress'
    assert collection.query().all() == [james]

    # Test search by gender
    collection.admissions = []
    collection.spoken_langs = None
    collection.written_langs = None

    lisa = create_translator(
        translator_app, email='lisa@memo.com', gender='F', last_name='L'
    )
    collection.genders = ['F']
    assert collection.query().all() == [lisa]
    collection.genders = ['M']
    assert collection.query().all() == [james, bob]

    collection.genders = []
    lisa.monitoring_languages.append(langs[2])
    collection.monitor_langs = [langs[2].id]
    assert collection.query().all() == [lisa]


def test_translator_collection_coordinates(translator_app):
    translators = TranslatorCollection(translator_app)
    trs = translators.add(
        **translator_data,
        coordinates=Coordinates()
    )
    # somehow, the instance has to be created in order to have deferred content
    # def add() would not have been overwritten
    assert trs.coordinates == Coordinates()


def test_translator_collection_wrong_user_input(translator_app):
    # Prevent wrong user input from going to the db query
    coll = TranslatorCollection(
        translator_app, order_by='nothing', order_desc='hey'
    )
    assert coll.order_desc is False
    assert coll.order_by == 'last_name'


def test_translator_collection_update(translator_app):
    session = translator_app.session()
    collection = TranslatorCollection(translator_app)
    users = UserCollection(session)

    # Create
    translator_a = collection.add(first_name='A', last_name='A', email=None)
    translator_b = collection.add(first_name='B', last_name='B', email='b@b.b')
    translator_x = collection.add(first_name='C', last_name='C', email='x@x.x',
                                  update_user=False)
    assert not translator_a.user
    assert translator_b.user.username == 'b@b.b'
    assert translator_b.user.role == 'translator'
    assert translator_b.user.active
    assert not translator_x.user

    # Correct role and state
    translator_b.user.active = False
    translator_b.user.role = 'member'
    session.flush()
    session.expire_all()
    collection.update_user(translator_a, translator_a.email)
    collection.update_user(translator_b, translator_b.email)
    session.flush()
    session.expire_all()
    assert not translator_a.user
    assert translator_b.user.username == 'b@b.b'
    assert translator_b.user.role == 'translator'
    assert translator_b.user.active

    # Add / Deactivate
    collection.update_user(translator_a, 'a@a.a')
    collection.update_user(translator_b, None)
    translator_a.email = 'a@a.a'
    translator_b.email = None
    session.flush()
    session.expire_all()
    user_b = users.by_username('b@b.b')
    assert translator_a.user.username == 'a@a.a'
    assert translator_a.user.role == 'translator'
    assert translator_a.user.active is True
    assert not translator_b.user
    assert not user_b.active

    # Delete / Reactivate
    user_b.role = 'member'
    session.flush()
    session.expire_all()
    collection.delete(translator_a)
    collection.update_user(translator_b, 'b@b.b')
    translator_b.email = 'b@b.b'
    session.flush()
    session.expire_all()
    user_a = users.by_username('a@a.a')
    assert not user_a.active
    assert not user_a.translator
    assert translator_b.user.username == 'b@b.b'
    assert translator_b.user.role == 'translator'
    assert translator_b.user.active

    # Change
    collection.update_user(translator_b, 'c@c.c')
    translator_b.email = 'c@c.c'
    session.flush()
    session.expire_all()
    assert translator_b.user.username == 'c@c.c'
    assert translator_b.user.role == 'translator'
    assert translator_b.user.active
    assert user_b.username == 'c@c.c'

    collection.update_user(translator_b, 'a@a.a')
    translator_b.email = 'a@a.a'
    session.flush()
    session.expire_all()
    assert translator_b.user.username == 'a@a.a'
    assert translator_b.user.role == 'translator'
    assert translator_b.user.active
    assert user_a.translator == translator_b
    assert not user_b.translator


def test_language_collection(session):
    coll = LanguageCollection(session)
    zulu = coll.add(name='Zulu')
    arabic = coll.add(name='Arabic')
    assert coll.query().all() == [arabic, zulu]


def test_translator_collection_visibility(translator_app):
    # Create a single translator marked as for_admins_only
    hidden_translator = create_translator(
        translator_app, email='hidden@example.com', last_name='Hidden',
        for_admins_only=True
    )

    # Scenario 1: Non-admin user (e.g., user_role='member')
    # Non-admins should never see translators marked as for_admins_only,
    # include_hidden is false by default
    # regardless of the include_hidden flag.
    coll_non_admin = TranslatorCollection(translator_app, user_role='member')
    assert coll_non_admin.query().count() == 0
    return

    coll_non_admin_include_true = TranslatorCollection(
        translator_app, user_role='member', include_hidden=True
    )
    assert hidden_translator not in coll_non_admin_include_true.query().all()

    # Scenario 2: Admin user (user_role='admin')
    # Admins should only see for_admins_only translators if include_hidden=True
    # Default (include_hidden = False): hidden translator should not be visible
    coll_admin_default = TranslatorCollection(
        translator_app, user_role='admin'
    )
    assert hidden_translator not in coll_admin_default.query().all()

    # Explicitly include_hidden = True: hidden translator should be visible
    coll_admin_include_true = TranslatorCollection(
        translator_app, user_role='admin', include_hidden=True
    )
    assert hidden_translator in coll_admin_include_true.query().all()
    assert len(coll_admin_include_true.query().all()) == 1
