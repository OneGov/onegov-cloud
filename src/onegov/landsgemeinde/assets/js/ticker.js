document.addEventListener("DOMContentLoaded", function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;

    function onWebsocketNotification(message, _websocket) {
        if (document.body.id.search(message.assembly) !== -1) {
            if (message.event === 'refresh') {
                window.location.reload();
            }
            if (message.event === 'update') {
                const node = document.getElementById(message.node);
                if (node && message.content) {
                    const content = document.createElement('div');
                    content.innerHTML = message.content;
                    node.replaceWith(content.firstChild);
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
