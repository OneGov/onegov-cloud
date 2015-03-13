from onegov.page import PageCollection
from onegov.town.model import Town


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
        meta={'type': 'town-root'}
    ),
    pages.add_root(
        'Kultur & Freizeit',
        name='kultur-freizeit',
        meta={'type': 'town-root'}
    ),
    pages.add_root(
        'Bildung & Gesellschaft',
        name='bildung-gesellschaft',
        meta={'type': 'town-root'}
    ),
    pages.add_root(
        'Gewerbe & Tourismus',
        name='gewerbe-tourismus',
        meta={'type': 'town-root'}
    ),
    pages.add_root(
        'Politik & Verwaltung',
        name='politik-verwaltung',
        meta={'type': 'town-root'}
    )

    session.flush()
