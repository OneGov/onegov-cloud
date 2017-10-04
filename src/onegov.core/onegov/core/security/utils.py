from onegov.core.browser_session import BrowserSession


def forget(app, session_id):
    """ Clears the tokens associated with the identity from given browser
    session.

    """

    session = BrowserSession(app.application_id, session_id, app.session_cache)
    for key in ('userid', 'role', 'application_id'):
        if session.has(key):
            del session[key]


def remembered(app, session_id):
    """ Checks if tokens associated with the identity are stored for the given
    browser session.

    """
    session = BrowserSession(app.application_id, session_id, app.session_cache)
    for key in ('userid', 'role', 'application_id'):
        if session.has(key):
            return True

    return False
