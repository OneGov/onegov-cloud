$(document).ready(function() {
    const endpoint = $('body').data('websocket-endpoint');
    const schema = $('body').data('websocket-schema');
    const fallback = $('body').data('websocket-fallback');

    function onWebsocketNotification(message, websocket) {
        if (message.event === 'refresh' && window.location.href.search(message.path) !== -1) {
            $(".page-refresh").show();
            websocket.close();
        }
    }

    var lastNotified;
    var intervalId;
    function poll() {
        if (fallback) {
            fetch(fallback)
                .then((response) => response.json())
                .then((data) => {
                    const notified = Date.parse(data['last-notified']) || 1;
                    if (lastNotified && notified !== lastNotified) {
                        $(".page-refresh").show();
                        clearInterval(intervalId);
                    }
                    lastNotified = notified;
                })
                .catch((_error) => {});
        }
    }

    function onWebsocketError(_event, websocket) {
        websocket.close();
        if (fallback) {
            intervalId = setInterval(poll, 60000);
        }
    }

    if (endpoint && schema) {
        openWebsocket(endpoint, schema, null, onWebsocketNotification, onWebsocketError);
    }
});
