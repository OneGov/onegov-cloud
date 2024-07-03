function scrollToCurrentItem() {
    if ($('#current').length) {
        const positionCurrent = $('#current').position().top - $('.agenda-item-list').position().top;
        const listHeight = $('.agenda-item-list').height();
        const currentHeight = $('#current').height();
        const scrollTopList = $('.agenda-item-list').scrollTop();

        $('.agenda-item-list').animate({
            scrollTop: positionCurrent - listHeight / 2 + currentHeight / 2 + scrollTopList
        });
    }
}

scrollToCurrentItem();

document.addEventListener("DOMContentLoaded", function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;

    function onWebsocketNotification(message, _websocket) {
        if (document.body.id.search(message.assembly) !== -1) {
            if (message.event === 'refresh') {
                window.location.reload();
            }
            if (message.event === 'update') {
                const agendaItem = document.getElementById(message.node);
                const agendaListItem = document.querySelector('#list-' + message.node + ' a');
                const currentAgendaListItem = document.getElementById('current');
                if (agendaItem && message.content) {
                    const content = document.createElement('div');
                    content.innerHTML = message.content;
                    agendaItem.replaceWith(content.firstChild);
                }
                if (message.state === 'scheduled') {
                    agendaListItem.classList.add('scheduled');
                    agendaListItem.id = '';
                }
                if (message.state === 'ongoing') {
                    agendaListItem.classList.remove('scheduled');
                    if (currentAgendaListItem) {
                        currentAgendaListItem.id = '';
                    }
                    agendaListItem.id = 'current';
                    agendaListItem.href = '#' + message.node;
                    scrollToCurrentItem();
                }
                if (message.state === 'completed') {
                    agendaListItem.classList.remove('scheduled');
                    agendaListItem.id = '';
                }
            }
        }
    }

    var lastModified;
    function poll() {
        fetch(window.location.href + '?' + new Date().getTime(), {method: "HEAD"})
            .then((response) => {
                const modified = response.headers.get("Last-Modified");
                if (lastModified && modified !== lastModified) {
                    window.location.reload();
                }
                lastModified = modified;
            })
            .catch((_error) => {});
    }
    poll();

    var intervalID;
    function initiatePolling() {
        if (!intervalID) {
            intervalID = setInterval(poll, 30 * 1000);
        }
    }

    function onWebsocketError(_event, websocket) {
        websocket.close();
        initiatePolling();
    }

    if (endpoint && schema) {
        const websocket = openWebsocket(
            endpoint,
            schema,
            null,
            onWebsocketNotification,
            onWebsocketError
        );
        websocket.addEventListener("close", function() {
            initiatePolling();
        });
    } else {
        initiatePolling();
    }
});
