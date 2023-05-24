$(document).ready(function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;

    function onWebsocketNotification(message, _websocket) {
        if (message.event === 'refresh' && document.body.id.search(message.assembly) !== -1) {
            window.location.reload();
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
