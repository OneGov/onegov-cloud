document.addEventListener("DOMContentLoaded", function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;
    const chatArea = document.getElementById("message-area");
    const customerName = chatArea.dataset.customerName;
    const chatWindow = document.getElementById("chat");
    const connecting = document.getElementById('connecting')
    var ended = document.getElementById('ended')

    const token = document.body.dataset.websocketToken

    function browserNotification(message) {
        if (!("Notification" in window)) {
          // Check if the browser supports notifications
            alert("This browser does not support desktop notification");
        } else if (Notification.permission === "granted") {
          // Check whether notification permissions have already been granted;
          // if so, create a notification
            const notification = new Notification(message);
        } else if (Notification.permission !== "denied") {
          // We need to ask the user for permission
          Notification.requestPermission().then((permission) => {
            // If the user accepts, let's create a notification
            if (permission === "granted") {
                const notification = new Notification(message);
            }
          });
        }
    }

    function onWebsocketNotification(message, _websocket) {
        message = JSON.parse(message)
        if (message.type == 'message') {
            connecting.style.display = "none"
            createChatBubble(message, message.userId == 'customer')

        } else if (message.type == 'accepted') {
            var aceptedNotification = document.getElementById('accepted')
            aceptedNotification.style.display = 'flex'
            // browserNotification(aceptedNotification.textContent)

        } else if (message.type == 'end-chat') {
            console.log('Staff ended chat')
            ended.style.display = 'flex'

        } else {
            console.log('unkown messaage type', message)
        }
    }

    function onWebsocketError(_event, websocket) {
        websocket.close();
    }

    function createChatBubble(message, self) {
        var chatCard = document.getElementsByClassName('chat-card')[0].cloneNode(true)
        chatCard.style.display = 'flex'
        chatCard.classList.add(self ? 'right' : 'left')
        chatCard.children[0].appendChild(document.createTextNode(message.user))
        chatCard.children[1].children[0].appendChild(document.createTextNode(message.text))
        chatCard.children[2].appendChild(document.createTextNode(message.time))
        chatArea.appendChild(chatCard);
    }

    if (endpoint && schema && token) {
        // NOTE: Includes schema with the WebSocket URL because the chat
        // requires the schema on initiation. This should be already done when
        // setting the data-websocket-endpoint. That however requires modifying
        // WebsocketsApp.
        const chatEndpoint = `${endpoint}/chats?schema=${schema}&token=${token}`

        const socket = openWebsocket(
            chatEndpoint,
            schema,
            null,
            onWebsocketNotification,
            onWebsocketError,
            'customer_chat',
        );

        console.log('i know the customer:', customerName)

        document.getElementById("send").addEventListener("click", () => {
            var now = new Date().toUTCString()
            var channelId = chatArea.dataset.chatId

            var messages = document.querySelectorAll('.chat-card');

            if (messages.length == 1) {
                connecting.style.display = "flex"
            }

            const payload = JSON.stringify({
                type: "message",
                text: chatWindow.value,
                user: customerName,
                userId: 'customer',
                channel: channelId,
                time: now,
            });

            console.log('im about to send ', payload)

            socket.send(payload);
            chatWindow.value = '';
        })
    }

});
