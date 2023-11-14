document.addEventListener("DOMContentLoaded", function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;
    const chatArea = document.getElementById("message-area");
    const staffName = chatArea.dataset.staffName;
    const staffId = chatArea.dataset.staffId;
    const chatWindow = document.getElementById("chat");

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

    function onWebsocketNotification(message, websocket) {
        message = JSON.parse(message)
        if (message.type == 'request') {
            // browserNotification(message.notification)
            var requestElement = document.getElementById('new-request')
            var requestList = document.getElementById('request-list')
            var newRequest = requestElement.cloneNode(true)
            var noRequestText = document.getElementById('no-request')

            newRequest.id = 'request-' + message.channel
            newRequest.style.display = 'block'
            newRequest.children[1].id = message.channel

            noRequestText.style.display = 'none'
            requestList.appendChild(newRequest)

            // Click on new request
            newRequest.children[1].addEventListener("click", () => {
                channel = message.channel
                acceptRequest(channel, websocket)
            })

        } else if (message.type == 'message') {
            createChatBubble(message, message.userId == staffId)

        } else if (message.type == 'accepted') {
            var aceptedNotification = document.getElementById('accepted')
            aceptedNotification.style.display = 'flex'

        } else if (message.type == 'chat-history') {
            // Display chat history
            removePreviousChat()
            chatArea.dataset.chatId = message.channel
            document.getElementById('chat_id').value = message.channel
            console.log('message-history', message)

            var messages = message.history;
            messages.forEach(m => {
                var no_chat_open = document.getElementById('no-chat-open')
                no_chat_open.style.display = 'none'
                var message_area = document.getElementById("message-area");
                message_area.style.display = 'flex'
                var chat_form = document.getElementById('chat-form')
                chat_form.style.display = 'flex'
                createChatBubble(m, m.userId == staffId)
            })
            document.getElementById('loading').style.display = 'none'
            document.getElementById('chat-actions').style.display = 'block'

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

    function removePreviousChat() {
        var templateMessage = document.getElementsByClassName('chat-card')[0].cloneNode(true)
        const previousMessages = document.querySelectorAll('.chat-card');
        console.log('pm', previousMessages)
        previousMessages.forEach(m => {
            m.remove()
        })
        chatArea.appendChild(templateMessage)
    }

    function acceptRequest(channel, websocket) {
        console.log('accepted request with channel:' + channel)
        // Display and hide elements
        document.getElementById('no-chat-open').style.display = 'none'
        chatArea.classList.add = channel
        chatArea.dataset.chatId = channel
        chatArea.style.display = 'flex'
        var chat_form = document.getElementById('chat-form')
        chat_form.style.display = 'block'
        var request = document.getElementById('request-' + channel)
        request.remove()
        document.getElementById('chat-actions').style.display = 'block'

        addActiveChat(channel)

        const payload = JSON.stringify({
            type: "accepted",
            userId: staffId,
            channel: channel
        });
        websocket.send(payload);
    }

    function addActiveChat(channel) {
        var activeChatElement = document.getElementById('new-active-chat')
        var newActiveChatElement = activeChatElement.cloneNode(true)
        console.log(newActiveChatElement)
        var activeChatList = document.getElementById('active-chat-list')
        newActiveChatElement.id = 'active-chat-' + channel
        newActiveChatElement.dataset.chatId = channel
        newActiveChatElement.style.display = 'block'
        userText = document.createTextNode('user')
        newActiveChatElement.children[0].children[0].appendChild(userText)
        activeChatList.appendChild(newActiveChatElement)
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

        //Click on pre loaded request
        const openRequests = document.querySelectorAll('.open-request');
        openRequests.forEach(request => {
            var channel = request.dataset.requestId
            request.addEventListener("click", () => {
                acceptRequest(channel, socket)
            })
        })

        // Click on active chat
        const activeChats = document.querySelectorAll('.active-chat');
        activeChats.forEach(chat => {
            var channel = chat.dataset.chatId
            chat.addEventListener("click", () => {
                console.log('open chat with id' + channel)
                chatArea.style.display = 'flex'
                document.getElementById('loading').style.display = 'flex'

                var payload = JSON.stringify({
                    type: 'request-chat-history',
                    channel: channel,
                });

                socket.send(payload);
            })
        })

        // Click on chat-actions
        var chatActions = document.getElementById('chat-actions')
        chatActions.addEventListener("submit", () => {
            var chatId = chatArea.dataset.chatId
            console.log('ending chat')
            console.log(chatArea.dataset)
            console.log(chatArea.dataset.chatId)
            var no_chat_open = document.getElementById('no-chat-open')
            no_chat_open.style.display = 'flex'

            removePreviousChat()
            document.getElementById('chat-form').style.display = 'none'
            document.getElementById('chat-actions').style.display = 'none'
            document.getElementById('active-chat-' + chatId).remove()

            var payload = JSON.stringify({
                type: 'end-chat',
                channel: chatId,
            });

            socket.send(payload);

            return true;
        })


        // Send single chat-message
        document.getElementById("send").addEventListener("click", () => {
            now = new Date().toUTCString()

            const payload = JSON.stringify({
                type: 'message',
                text: chatWindow.value,
                user: staffName,
                userId: staffId,
                time: now,
            });

            socket.send(payload);
            chatWindow.value = '';
        })
    }
});
