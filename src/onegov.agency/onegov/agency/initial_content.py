from onegov.core.utils import module_path
from onegov.org.initial_content import load_content, add_pages
from onegov.org.models import Organisation


def create_new_organisation(app, name, locale='de_CH'):
    assert locale == 'de_CH'

    path = module_path('onegov.agency', 'content/de.yaml')
    content = load_content(path)

    org = Organisation(name=name, **content['organisation'])
    org.meta['locales'] = locale

    session = app.session()
    session.add(org)

    add_pages(session, path)

    return org
