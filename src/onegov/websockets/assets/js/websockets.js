var openWebsocket = function(endpoint, schema, channel, onNotifcation, onError, eventType) {
    const websocket = new WebSocket(endpoint);
    websocket.addEventListener("open", function() {
        const payload = {
            type: eventType||"register",
            schema: schema,
            channel: channel
        };
        websocket.send(JSON.stringify(payload));
    });
    websocket.addEventListener('message', function(message) {
        const data = JSON.parse(message.data);
        if (data.type === 'notification') {
            onNotifcation(data.message, websocket);
        }
        if (data.type === 'error' && onError) {
            onError(data.message, websocket);
        }
    });
    return websocket;
};
