document.addEventListener("DOMContentLoaded", function() {
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

    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;
    const chatArea = document.getElementById("message-area");
    const staffName = chatArea.dataset.staffName;
    const staffId = chatArea.dataset.staffId;
    const chatWindow = document.getElementById("chat");

    function onWebsocketNotification(message, websocket) {
        message = JSON.parse(message)
        if (message.type == 'request') {
            browserNotification(message.text)

            // Add request element
            var requestElement = document.getElementById('new-request')
            var newRequest = requestElement.cloneNode(true)
            newRequest.id = ''
            newRequest.style.display = 'block'
            newRequest.children[1].id = message.channel
            var requestList = document.getElementById('request-list')
            var noRequestText = document.getElementById('no-request')
            noRequestText.style.display = 'none'
            requestList.appendChild(newRequest)

            newRequest.children[1].addEventListener("click", () => {

                // Show chat window for open chat and remove request
                var no_chat_open = document.getElementById('no-chat-open')
                no_chat_open.style.display = 'none'
                var message_area = document.getElementById("message-area");
                message_area.classList.add = message.channel
                message_area.style.display = 'flex'
                var chat_form = document.getElementById('chat-form')
                chat_form.style.display = 'block'
                newRequest.remove()
                noRequestText.style.display = 'block'

                document.getElementById('chat-options').style.display = 'block'

                const payload = JSON.stringify({
                    type: "accepted",
                    text: "Anfrage wurde angenommen",
                    id: staffId,
                    channel: message.channel
                });

                websocket.send(payload);
            })
        } else if (message.type == 'message') {
            createChatBubble(message, message.id == staffId)
        } else if (message.type == 'accepted') {
            var aceptedNotification = document.getElementById('accepted')
            aceptedNotification.style.display = 'flex'
        } else if (message.type == 'chat-history') {
            // Display chat history
            var templateMessage = document.getElementsByClassName('chat-card')[0].cloneNode(true)
            const previousMessages = document.querySelectorAll('.chat-card');
            console.log('pm', previousMessages)
            previousMessages.forEach(m => {
                m.remove()
            })
            chatArea.appendChild(templateMessage)

            var messages = message.text;
            messages.forEach(m => {
                var no_chat_open = document.getElementById('no-chat-open')
                no_chat_open.style.display = 'none'
                var message_area = document.getElementById("message-area");
                message_area.style.display = 'flex'
                var chat_form = document.getElementById('chat-form')
                chat_form.style.display = 'flex'
                createChatBubble(m, m.id == staffId)
            })
            document.getElementById('loading').style.display = 'none'
            document.getElementById('chat-options').style.display = 'block'
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

    if (endpoint && schema) {
        const socket = openWebsocket(
            endpoint,
            schema,
            null,
            onWebsocketNotification,
            onWebsocketError,
            'staff_chat'
        );

        // Click on active chat
        const activeChats = document.querySelectorAll('.active-chat');
        activeChats.forEach(chat => {
            var requestId = chat.dataset.chatId
            chat.addEventListener("click", () => {
                console.log(document.getElementById('loading'))
                document.getElementById('loading').style.display = 'flex'

                var payload = JSON.stringify({
                    type: 'request-chat-history',
                    id: requestId,
                });

                socket.send(payload);
            })
        })

        document.getElementById("send").addEventListener("click", () => {
            now = new Date().toUTCString()

            const payload = JSON.stringify({
                type: 'message',
                text: chatWindow.value,
                user: staffName,
                id: staffId,
                time: now,
            });

            socket.send(payload);
            chatWindow.value = '';
        })
    }
});
