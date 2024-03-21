from onegov.core.utils import module_path
from onegov.org.initial_content import load_content
from onegov.org.models import Organisation


def create_new_organisation(app, name, reply_to=None, forms=None,
                            create_files=True, path=None, locale='de_CH'):

    session = app.session()

    locales = {'de_CH': 'content/de.yaml'}

    path = path or module_path('onegov.landsgemeinde', locales[locale])
    content = load_content(path)

    # can only be called if no organisation is defined yet
    assert not session.query(Organisation).first()

    org = Organisation(name=name, **content['organisation'])
    org.reply_to = reply_to
    org.meta['locales'] = locale
    session.add(org)

    session.flush()
