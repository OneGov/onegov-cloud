document.addEventListener("DOMContentLoaded", function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;

    function onWebsocketNotification(message, _websocket) {
        message = JSON.parse(message)
        createChatBubble(message.text, false)
    }

    function onWebsocketError(_event, websocket) {
        websocket.close();
    }

    function createChatBubble(message, self) {
        const chatArea = document.getElementById("message-area");
        
        // Create the parts
        var card = document.createElement("div")
        if (self) {
            card.classList.add("card", "right");
        } else {
            card.classList.add("card", "left");
        }
        var section = document.createElement("div")
        section.classList.add('card-section');
        var textNode = document.createElement("p");
        var timeNode = document.createElement("p");
        timeNode.classList.add('info');
        now = new Date().toUTCString()
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
            'staff_chat'
        );

        const chatArea = document.getElementById("message-area");
        const customerName = chatArea.dataset.customerName;
        console.log(customerName)
        const chatWindow = document.getElementById("chat");

        document.getElementById("send").addEventListener("click", () => {

            createChatBubble(chatWindow.value, true)

            const payload = JSON.stringify({
                type: "message",
                text: chatWindow.value,
                user: customerName,
                time: now,
            });

            socket.send(payload);
            chatWindow.value = '';
        })
    }
});
