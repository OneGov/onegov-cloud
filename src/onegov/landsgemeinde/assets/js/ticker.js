$(document).ready(function() {
    const endpoint = $('body').data('websocket-endpoint');
    const schema = $('body').data('websocket-schema');

    function onWebsocketNotification(message, _websocket) {
        if (message.event === 'refresh' && window.location.href.search(message.path) !== -1) {
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
        setInterval(poll, 60000);
    }

    if (endpoint && schema) {
        openWebsocket(endpoint, schema, null, onWebsocketNotification, onWebsocketError);
    }
});
