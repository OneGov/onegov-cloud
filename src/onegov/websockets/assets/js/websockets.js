var openWebsocket = function(endpoint, schema, channel, onnotifcation) {
    const websocket = new WebSocket(endpoint);
    websocket.addEventListener("open", function() {
        const payload = {
            type: "register",
            schema: schema,
            channel: channel
        };
        websocket.send(JSON.stringify(payload));
    });
    websocket.addEventListener('message', function(message) {
        const data = JSON.parse(message.data);
        if (data.type === 'notification') {
            onnotifcation(data.message, websocket);
        }
    });
};
