# -*- coding: utf-8 -*-

import codecs
import os

from onegov.core.utils import module_path
from onegov.form import FormCollection
from onegov.page import PageCollection
from onegov.town.const import NEWS_PREFIX
from onegov.town.models import Town


def add_initial_content(session, town_name):
    """ Adds the initial content for the given town on the given session.

    All content that comes with a new town is added here.

    """

    # can only be called if no town is defined yet
    assert not session.query(Town).first()

    session.add(Town(name=town_name))

    add_root_pages(session)
    add_builtin_forms(session)

    session.flush()


def add_root_pages(session):
    pages = PageCollection(session)

    pages.add_root(
        "Leben & Wohnen",
        name='leben-wohnen',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        "Kultur & Freizeit",
        name='kultur-freizeit',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        "Bildung & Gesellschaft",
        name='bildung-gesellschaft',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        "Gewerbe & Tourismus",
        name='gewerbe-tourismus',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        "Politik & Verwaltung",
        name='politik-verwaltung',
        type='topic',
        meta={'trait': 'page'}
    )
    pages.add_root(
        "Aktuelles",
        name=NEWS_PREFIX,
        type='news',
        meta={'trait': 'news'}
    )


def add_builtin_forms(session):
    forms = FormCollection(session).definitions
    builtin_forms = module_path('onegov.town', 'forms')

    def load_definition(filename):
        path = os.path.join(builtin_forms, filename)
        with codecs.open(path, 'r', encoding='utf-8') as formfile:
            formlines = formfile.readlines()

            title = formlines[0].strip()
            definition = u''.join(formlines[3:])

            return title, definition

    def ensure_form(name, title, definition):
        form = forms.by_name(name)

        if form:
            form.title = title
            form.definition = definition
            form.type = 'builtin'
        else:
            forms.add(
                name=name,
                title=title,
                definition=definition,
                type='builtin'
            )

    for filename in os.listdir(builtin_forms):
        if filename.endswith('.form'):
            name = filename.replace('.form', '')
            title, definition = load_definition(filename)

            ensure_form(name, title, definition)
