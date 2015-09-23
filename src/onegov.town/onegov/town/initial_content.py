# -*- coding: utf-8 -*-

import codecs
import os

from datetime import datetime, timedelta
from onegov.core.utils import module_path
from onegov.event import EventCollection
from onegov.form import FormCollection
from onegov.libres import LibresIntegration, ResourceCollection
from onegov.page import PageCollection
from onegov.town.models import Town
from sedate import as_datetime


def add_initial_content(libres_registry, session_manager, town_name,
                        form_definitions=None):
    """ Adds the initial content for the given town on the given session.
    All content that comes with a new town is added here.

    Note, the ``form_definitions`` parameter is used to speed up testing,
    you usually do not want to specify it.

    """

    session = session_manager.session()

    libres_context = LibresIntegration.libres_context_from_session_manager(
        libres_registry, session_manager)

    # can only be called if no town is defined yet
    assert not session.query(Town).first()

    session.add(Town(name=town_name))

    add_root_pages(session)
    add_builtin_forms(session, form_definitions)
    add_resources(libres_context)
    add_events(session)

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
        name='aktuelles',
        type='news',
        meta={'trait': 'news'}
    )


def add_builtin_forms(session, definitions=None):
    forms = FormCollection(session).definitions
    definitions = definitions or builtin_form_definitions()

    for name, title, definition in definitions:
        form = forms.by_name(name)

        if form:
            # update
            form.title = title
            form.definition = definition
        else:
            # add
            form = forms.add(
                name=name,
                title=title,
                definition=definition,
                type='builtin'
            )

        assert form.form_class().has_required_email_field, (
            "Each form must have at least one required email field"
        )


def builtin_form_definitions(path=None):
    """ Yields the name, title and the form definition of all form definitions
    in the given or the default path.

    """
    path = path or module_path('onegov.town', 'forms')

    for filename in os.listdir(path):
        if filename.endswith('.form'):
            name = filename.replace('.form', '')
            title, definition = load_definition(os.path.join(path, filename))
            yield name, title, definition


def load_definition(path):
    """ Loads the title and the form definition from the given file. """

    with codecs.open(path, 'r', encoding='utf-8') as formfile:
        formlines = formfile.readlines()

        title = formlines[0].strip()
        definition = u''.join(formlines[3:])

        return title, definition


def add_resources(libres_context):
    resource = ResourceCollection(libres_context)
    resource.add(
        "SBB-Tageskarte",
        'Europe/Zurich',
        type='daypass',
        name='sbb-tageskarte'
    )


def add_events(session):
    start = as_datetime(datetime.today().date())
    while start.weekday() != 6:
        start = start + timedelta(days=1)

    events = EventCollection(session)
    event = events.add(
        title=u"150 Jahre Govikon",
        start=start + timedelta(hours=11, minutes=0),
        end=start + timedelta(hours=22, minutes=0),
        timezone="Europe/Zurich",
        tags=["Party"],
        location=u"Sportanlage",
        content={"description": u"Lorem ipsum."},
        meta={"submitter_email": u"info@example.org"},
    )
    event.submit()
    event.publish()
    event = events.add(
        title=u"Gemeindeversammlung",
        start=start + timedelta(days=2, hours=20, minutes=0),
        end=start + timedelta(days=2, hours=22, minutes=30),
        timezone="Europe/Zurich",
        tags=["Politics"],
        location=u"Gemeindesaal",
        content={"description": u"Lorem ipsum."},
        meta={"submitter_email": u"info@example.org"},
    )
    event.submit()
    event.publish()
    event = events.add(
        title=u"MuKi Turnen",
        start=start + timedelta(days=2, hours=10, minutes=0),
        end=start + timedelta(days=2, hours=11, minutes=0),
        recurrence=(
            "RRULE:FREQ=WEEKLY;WKST=MO;BYDAY=TU,TH;UNTIL={0}".format(
                (start + timedelta(days=31)).strftime('%Y%m%dT%H%M%SZ')
            )
        ),
        timezone="Europe/Zurich",
        tags=["Sports"],
        location=u"Turnhalle",
        content={"description": u"Lorem ipsum."},
        meta={"submitter_email": u"info@example.org"},
    )
    event.submit()
    event.publish()
    event = events.add(
        title=u"Grümpelturnier",
        start=start + timedelta(days=7, hours=10, minutes=0),
        end=start + timedelta(days=7, hours=18, minutes=0),
        timezone="Europe/Zurich",
        tags=["Sports"],
        location=u"Sportanlage",
        content={"description": u"Lorem ipsum."},
        meta={"submitter_email": u"info@example.org"},
    )
    event.submit()
    event.publish()
