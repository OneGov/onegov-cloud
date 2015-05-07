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

    pages = PageCollection(session)

    pages.add_root(
        'Leben & Wohnen',
        name='leben-wohnen',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        'Kultur & Freizeit',
        name='kultur-freizeit',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        'Bildung & Gesellschaft',
        name='bildung-gesellschaft',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        'Gewerbe & Tourismus',
        name='gewerbe-tourismus',
        type='topic',
        meta={'trait': 'page'}
    ),
    pages.add_root(
        'Politik & Verwaltung',
        name='politik-verwaltung',
        type='topic',
        meta={'trait': 'page'}
    )
    pages.add_root(
        'Aktuelles',
        name=NEWS_PREFIX,
        type='news',
        meta={'trait': 'news'}
    )

    session.flush()
