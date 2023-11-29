document.addEventListener("DOMContentLoaded", function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;
    const chatArea = document.getElementById("message-area");
    const chatForm = document.getElementById("chat-form");
    const customerName = chatArea.dataset.customerName;
    const chatWindow = document.getElementById("chat");
    const connecting = document.getElementById('connecting');
    var ended = document.getElementById('ended');
    var endedByTimeoutNotification = document.getElementById('ended-by-timeout');
    var acceptedNotification = document.getElementById('accepted');
    var accepted = document.getElementById('accepted');
    var startInformation = document.getElementById('start');
    const token = document.body.dataset.websocketToken;
    var chatActive = chatArea.dataset.chatActive;
    var messages = document.querySelectorAll('.chat-card');
    var endChatTimer;
    var firstMessageTimeout = 60000;
    var messageTimeout = 1800000;

    function notifyChatEnded() {
        var notification = endedByTimeoutNotification.cloneNode(true);
        notification.style.display = "block";
        chatArea.appendChild(notification);

        clearTimeout(endChatTimer);
    }

    if (chatActive == 'True' && messages.length == 2) {
        endChatTimer = setTimeout(notifyChatEnded, firstMessageTimeout);
    } else if (chatActive == 'True' && messages.length > 2) {
        endChatTimer = setTimeout(notifyChatEnded, messageTimeout);
    }

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
        message = JSON.parse(message);

        if (message.type == 'message') {
            connecting.style.display = "none";
            createChatBubble(message, message.userId == 'customer');
            var message_area = document.getElementById('message-area');
            message_area.scrollTop = message_area.scrollHeight;

        } else if (message.type == 'accepted') {
            var notification = accepted.cloneNode(true);
            chatArea.appendChild(notification);
            acceptedNotification.style.display = 'block';
            // browserNotification(acceptedNotification.textContent)

        } else if (message.type == 'end-chat') {
            clearTimeout(endChatTimer);
            ended = ended.cloneNode(true);
            chatArea.appendChild(ended);
            ended.style.display = 'block';
            chat.style.display = 'block';
            chatForm.remove();
        } else {
            console.log('unkown message type', message);
        }

        // Clear and restart the timer
        clearTimeout(endChatTimer);
        if (chatActive == true && messages.length == 2) {
            endChatTimer = setTimeout(notifyChatEnded, firstMessageTimeout);
        } else {
            endChatTimer = setTimeout(notifyChatEnded, messageTimeout);
        }
    }

    function onWebsocketError(_event, websocket) {
        websocket.close();
    }

    function createChatBubble(message, self) {
        var chatCard = document.getElementsByClassName('chat-card')[0].cloneNode(true);
        chatCard.style.display = 'block';
        chatCard.classList.add(self ? 'right' : 'left');
        chatCard.children[0].appendChild(document.createTextNode(message.user));
        chatCard.children[1].children[0].appendChild(document.createTextNode(message.text));
        chatCard.children[2].appendChild(document.createTextNode(message.time));
        chatArea.appendChild(chatCard);
    }

    if (endpoint && schema && token) {
        // NOTE: Includes schema with the WebSocket URL because the chat
        // requires the schema on initiation. This should be already done when
        // setting the data-websocket-endpoint. That however requires modifying
        // WebsocketsApp.
        const chatEndpoint = `${endpoint}/chats?schema=${schema}&token=${token}`;

        const socket = openWebsocket(
            chatEndpoint,
            schema,
            null,
            onWebsocketNotification,
            onWebsocketError,
            'customer_chat'
        );


        var message_area = document.getElementById('message-area');
        message_area.scrollTop = message_area.scrollHeight;

        document.getElementById("send").addEventListener("click", () => {
            const chatMessage = chatWindow.value;

            if (isEmpty(chatMessage)) {
                console.debug("Not sending empty message.");
                return;
            }

            var now = new Date();
            var hour =  now.getHours().toString().padStart(2, '0');
            var minute =  now.getMinutes().toString().padStart(2, '0');
            now = hour + ':' + minute;
            var channelId = chatArea.dataset.chatId;

            var messages = document.querySelectorAll('.chat-card');

            if (messages.length == 1) {
                connecting.style.display = "block";
                startInformation.style.display = "none";
            }

            const payload = JSON.stringify({
                type: "message",
                text: chatWindow.value,
                user: customerName,
                userId: 'customer',
                channel: channelId,
                time: now
            });

            socket.send(payload);
            chatWindow.value = '';
        });
    }

});
