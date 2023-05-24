from onegov.core.templates import render_macro
from onegov.landsgemeinde.layouts import DefaultLayout
from re import sub


def update_ticker(request, assembly, agenda_item=None, action='refresh'):
    assembly.stamp()
    content = ''
    if action == 'update' and agenda_item:
        layout = DefaultLayout(request.app, request)
        content = render_macro(
            layout.macros['ticker_agenda_item'],
            request,
            {
                'agenda_item': agenda_item,
                'layout': layout,
            }
        )
        content = sub(r'\s+', ' ', content)
        content = content.replace('> ', '>').replace(' <', '<')
        request.app.send_websocket({
            'event': action,
            'assembly': assembly.date.isoformat(),
            'node': f'agenda-item-{agenda_item.number}',
            'content': content
        })
    elif action == 'refresh':
        request.app.send_websocket({
            'event': 'refresh',
            'assembly': assembly.date.isoformat(),
        })
