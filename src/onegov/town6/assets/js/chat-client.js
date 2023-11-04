document.addEventListener("DOMContentLoaded", function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;

    function onWebsocketNotification(message, _websocket) {
        console.log('Ich ha öpis becho!')
        createChatBubble('de text')
        console.log(message)
        console.log(message.text)
    }

    function onWebsocketError(_event, websocket) {
        websocket.close();
    }

    function createChatBubble(message) {
        const chatArea = document.getElementById("message-area");

        // Create the parts
        var card = document.createElement("div")
        card.classList.add("card", "customer");
        var section = document.createElement("div")
        section.classList.add('card-section');
        var textNode = document.createElement("p");
        var timeNode = document.createElement("p");
        timeNode.classList.add('info');
        const time = document.createTextNode(now);
        const text = document.createTextNode(message);
        
        timeNode.appendChild(time);
        card.appendChild(section);
        section.appendChild(textNode);
        textNode.appendChild(text);
        card.appendChild(timeNode);
        chatArea.appendChild(card);
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

        const chatArea = document.getElementById("message-area");
        const customerName = chatArea.dataset.customerName;
        console.log(customerName)
        const chatWindow = document.getElementById("chat");


        document.getElementById("send").addEventListener("click", () => {
            now = new Date().toUTCString()

            createChatBubble(chatWindow.value)

            const payload = JSON.stringify({
                type: "message",
                message: chatWindow.value,
                user: customerName,
                time: now,
            });

            socket.send(payload);
        })
    }
});
