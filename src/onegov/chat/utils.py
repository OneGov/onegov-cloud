from urllib.parse import parse_qs, urlparse


def update_ticker(request, updated):
    """ Updates the ticker by a set of updated assemblies, agenda items or
    vota.

    Sends either a 'refresh' event to reload the whole ticker (in case the
    assembly has been changed or an agenda item has been added/deleted) or
    and 'update' event with the changed content of the agenda item.

    """


def send_message(request, text: str, chat_partner: str, datetime: str):
    request.app.send_websocket({
        'text': text,
        'chat_partner': chat_partner,
        'datetime': datetime,
    })


def param_from_path(name: str, path: str) -> str:
    """
    Retrieve any query parameter from a path.

    Raises ValueError if path is not a valid URL path or if it does not contain
    exactly one query parameter named `name`. Multiple parameters with that
    name are not supported and will result in ValueError, as it hints to a
    misconfiguration.

    Example:
        >>> schema_from_path("schema", "/chats?schema=onegov_town6-meggen")
        'onegov_town6-meggen

    """
    url = urlparse(path)
    query = parse_qs(url.query)

    if name not in query:
        raise ValueError(
            f"No parameter named {name} found in path: '{path}'."
        )

    if len(query[name]) != 1:
        raise ValueError(
            f"There must only be one instance of '{name}' in path: '{path}'."
        )

    return query[name][0]
