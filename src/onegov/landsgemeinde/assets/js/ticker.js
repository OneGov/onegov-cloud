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
        fetch(window.location.href, {method: "HEAD"})
            .then((response) => {
                const modified = response.headers.get("Last-Modified");
                if (lastModified && modified !== lastModified) {
                    window.location.reload();
                }
                lastModified = modified;
            })
            .catch((_error) => {});
    }

    function onWebsocketError(_event, websocket) {
        websocket.close();
        poll();
        setInterval(poll, 30 * 1000);
    }

    if (endpoint && schema) {
        openWebsocket(endpoint, schema, null, onWebsocketNotification, onWebsocketError);
    }
});
