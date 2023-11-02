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
