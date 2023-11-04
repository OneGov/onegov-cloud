document.addEventListener("DOMContentLoaded", function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;

    function onWebsocketNotification(message, _websocket) {
        console.log('Ich ha öpis becho!')
        console.log(message)
        console.log(message.text)
    }

    function onWebsocketError(_event, websocket) {
        websocket.close();
    }

    if (endpoint && schema) {
        const socket = openWebsocket(
            endpoint,
            schema,
            null,
            onWebsocketNotification,
            onWebsocketError,
            'chat'
        );

        document.getElementById("send").addEventListener("click", () => {
            const chatWindow = document.getElementById("chat");
            now = new Date().toUTCString()

            const payload = JSON.stringify({
                type: "message",
                message: chatWindow.value,
                user: "Haku",
                time: now,
            });

            socket.send(payload);

        })
    }
});
