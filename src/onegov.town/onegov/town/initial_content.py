from onegov.core.utils import module_path
from onegov.reservation import ResourceCollection
from onegov.org.initial_content import add_builtin_forms
from onegov.org.initial_content import builtin_form_definitions
from onegov.org.initial_content import add_filesets, add_pages, load_content
from onegov.org.initial_content import add_events
from onegov.org.models import Organisation


def create_new_organisation(app, name, reply_to=None, forms=None,
                            create_files=True, path=None, locale='de_CH'):
    session = app.session()

    locales = {
        'de_CH': 'content/de.yaml',
        'fr_CH': 'content/fr.yaml',
    }

    path = path or module_path('onegov.town', locales[locale])
    content = load_content(path)

    # can only be called if no organisation is defined yet
    assert not session.query(Organisation).first()

    org = Organisation(name=name, **content['organisation'])
    org.reply_to = reply_to
    org.meta['locales'] = locale
    session.add(org)

    form_locales = {
        'de_CH': 'forms/builtin/de',
        'fr_CH': 'forms/builtin/fr',
    }

    forms = forms or builtin_form_definitions(
        module_path('onegov.town', form_locales[locale]))

    translator = app.translations.get(locale)

    def translate(text):
        return text.interpolate(translator.gettext(text))

    add_pages(session, path)
    add_builtin_forms(session, forms)
    add_resources(app.libres_context)
    add_events(session, name, translate)

    if create_files:
        add_filesets(session, name, path)

    session.flush()


def add_resources(libres_context):
    resource = ResourceCollection(libres_context)
    resource.add(
        "SBB-Tageskarte",
        'Europe/Zurich',
        type='daypass',
        name='sbb-tageskarte'
    )
