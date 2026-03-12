document.addEventListener("DOMContentLoaded", function() {
    const endpoint = document.body.dataset.websocketEndpoint;
    const schema = document.body.dataset.websocketSchema;
    const chatArea = document.getElementById("message-area");
    const staffName = chatArea.dataset.staffName;
    const staffId = chatArea.dataset.staffId;
    const chatWindow = document.getElementById("chat");
    const token = document.body.dataset.websocketToken;
    const activeChats = document.querySelectorAll('.active-chat');
    var aceptedNotification = document.getElementById('accepted');
    var noRequestText = document.getElementById('no-request');
    var noActiveChatsText = document.getElementById('no-active-chats');
    var requestList = document.getElementById('request-list');

    if (endpoint && schema && token) {
        const chatEndpoint = `${endpoint}/chats?token=${token}`;

        function showElement(element, display = 'block') { element.style.display = display; }
        function hideElement(element) { element.style.display = 'none'; }

        function getChatBlobFor(chatId) {
            const selector = 'active-chat-' + chatId;
            const blob = document.getElementById(selector).children[0].children[0];

            if (!blob) {
                // eslint-disable-next-line no-console
                console.error("Unable to find chat blob for chat: " + chatId);
                return null;
            }

            return blob;
        }

        // eslint-disable-next-line consistent-this
        function createChatBubble(message, self) {
            var chatCard = document.getElementsByClassName('chat-card')[0].cloneNode(true);
            chatCard.style.display = 'block';
            chatCard.classList.add(self ? 'right' : 'left');
            chatCard.children[0].appendChild(document.createTextNode(message.user));
            chatCard.children[1].children[0].appendChild(document.createTextNode(message.text));
            chatCard.children[2].appendChild(document.createTextNode(message.time));
            chatArea.appendChild(chatCard);
        }

        function removePreviousChat() {
            var templateMessage = document.getElementsByClassName('chat-card')[0].cloneNode(true);
            const previousMessages = document.querySelectorAll('.chat-card');
            previousMessages.forEach((m) => {
                m.remove();
            });
            chatArea.appendChild(templateMessage);
        }

        function requestHistory(chat) {
            var channel = chat.dataset.chatId;
            chat.addEventListener("click", () => {
                // eslint-disable-next-line no-console
                console.log('open chat with id' + channel);
                chatArea.style.display = 'block';
                document.getElementById('loading').style.display = 'block';

                var payload = JSON.stringify({
                    type: 'request-chat-history',
                    channel: channel
                });

                // eslint-disable-next-line no-use-before-define
                socket.send(payload);
            });
        }

        function addActiveChat(channel, user) {
            var activeChatElement = document.getElementById('new-active-chat');
            var newActiveChatElement = activeChatElement.cloneNode(true);
            var activeChatList = document.getElementById('active-chat-list');
            newActiveChatElement.id = 'active-chat-' + channel;
            newActiveChatElement.dataset.chatId = channel;
            newActiveChatElement.style.display = 'block';
            userText = document.createTextNode(user);
            newActiveChatElement.children[0].children[1].appendChild(userText);
            activeChatList.appendChild(newActiveChatElement);
            requestHistory(newActiveChatElement);
        }

        function acceptRequest(channel, user, websocket) {
            // Display and hide elements
            document.getElementById('no-chat-open').style.display = 'none';
            chatArea.classList.add = channel;
            chatArea.dataset.chatId = channel;
            chatArea.style.display = 'block';
            var chat_form = document.getElementById('chat-form');
            chat_form.style.display = 'block';
            var request = document.getElementById('request-' + channel);
            request.remove();
            document.getElementById('chat-actions').style.display = 'block';

            addActiveChat(channel, user);

            const payload = JSON.stringify({
                type: "accepted",
                userId: staffId,
                channel: channel
            });
            websocket.send(payload);
        }

        function onWebsocketNotification(message, websocket) {
            message = JSON.parse(message);
            if (message.type === 'request') {
            // browserNotification(message.notification)
                var requestElement = document.getElementById('new-request');
                var newRequest = requestElement.cloneNode(true);

                newRequest.id = 'request-' + message.channel;
                newRequest.style.display = 'block';
                var userText = document.createTextNode(message.user);
                newRequest.children[0].appendChild(userText);
                var topicText = document.createTextNode(message.topic);
                newRequest.children[1].appendChild(topicText);

                noRequestText.style.display = 'none';
                requestList.appendChild(newRequest);

                // Click on new request
                newRequest.addEventListener("click", () => {
                    acceptRequest(message.channel, message.user, websocket);
                });

            } else if (message.type === 'message') {
                if (chatArea.dataset.chatId === message.channel) {
                    createChatBubble(message, message.userId === staffId);
                    chatArea.scrollTop = chatArea.scrollHeight;
                } else {
                    const chatBlob = getChatBlobFor(message.channel);

                    if (chatBlob) {
                        showElement(chatBlob);
                    }
                }
            } else if (message.type === 'hide-request') {
                var request = document.getElementById('request-' + message.channel);
                request.remove();
                if (requestList.children.length < 2) {
                    noRequestText.style.display = 'block';
                }

            } else if (message.type === 'chat-history') {
            // Display chat history
                removePreviousChat();
                chatArea.dataset.chatId = message.channel;
                document.getElementById('chat_id').value = message.channel;

                var messages = message.history;
                messages.forEach((m) => {
                    var no_chat_open = document.getElementById('no-chat-open');
                    no_chat_open.style.display = 'none';
                    chatArea.style.display = 'block';
                    var chat_form = document.getElementById('chat-form');
                    chat_form.style.display = 'flex';
                    createChatBubble(m, m.userId === staffId);
                });
                aceptedNotification.style.display = 'block';
                document.getElementById('loading').style.display = 'none';
                document.getElementById('chat-actions').style.display = 'block';
                if (requestList.children.length < 2) {
                    noRequestText.style.display = 'block';
                }
                noActiveChatsText.style.display = 'none';

                const chatBlob = getChatBlobFor(message.channel);
                if (chatBlob) {
                    hideElement(chatBlob);
                }
                chatArea.scrollTop = chatArea.scrollHeight;
            } else {
                // eslint-disable-next-line no-console
                console.log('unkown messaage type', message);
            }
        }

        function onWebsocketError(_event, websocket) {
            websocket.close();
        }

        const socket = openWebsocket(
            chatEndpoint,
            schema,
            null,
            onWebsocketNotification,
            onWebsocketError,
            'staff_chat'
        );

        function getCurrentChatId() {
            return chatArea.dataset.chatId || null;
        }

        // Run function when websocket is ready.
        function websocketReady(fn) {
            if (socket.readyState === WebSocket.OPEN) {
                fn();
            } else {
                socket.addEventListener("open", fn);
            }
        }

        // Click on pre loaded request
        const openRequests = document.querySelectorAll('.open-request');
        openRequests.forEach((request) => {
            var requestDataset = request.dataset;
            request.addEventListener("click", () => {
                acceptRequest(requestDataset.requestId, requestDataset.user, socket);
            });
        });

        // Reconnect to active chats once websocket is established.
        websocketReady(function() {
        // Active Chats
            activeChats.forEach((chat) => {
                if (chat.id !== 'new-active-chat') {
                    var channel = chat.dataset.chatId;
                    var payloadReconnect = JSON.stringify({
                        type: 'reconnect',
                        channel: channel
                    });

                    socket.send(payloadReconnect);
                }

                requestHistory(chat); // Function has an event listener
            });
        });

        websocketReady(function() {
            // eslint-disable-next-line no-console
            console.debug("websocket is established");
        });

        // Click on chat-actions
        var chatActions = document.getElementById('chat-actions');
        chatActions.addEventListener("submit", () => {
            var chatId = chatArea.dataset.chatId;
            // eslint-disable-next-line no-console
            console.log('ending chat');
            var no_chat_open = document.getElementById('no-chat-open');
            no_chat_open.style.display = 'flex';

            removePreviousChat();
            document.getElementById('chat-form').style.display = 'none';
            document.getElementById('chat-actions').style.display = 'none';
            document.getElementById('active-chat-' + chatId).remove();

            var payload = JSON.stringify({
                type: 'end-chat',
                channel: chatId
            });

            socket.send(payload);

            return true;
        });

        // Send single chat-message
        document.getElementById("send").addEventListener("click", () => {
            const chatMessage = chatWindow.value;

            if (isEmpty(chatMessage)) {
                // eslint-disable-next-line no-console
                console.debug("Not sending empty message.");
                return;
            }

            var now = new Date();
            var hour =  now.getHours().toString().padStart(2, '0');
            var minute =  now.getMinutes().toString().padStart(2, '0');
            now = hour + ':' + minute;

            const payload = JSON.stringify({
                type: 'message',
                text: chatMessage,
                user: staffName,
                userId: staffId,
                time: now,
                channel: getCurrentChatId()
            });

            socket.send(payload);
            chatWindow.value = '';

        });
    }
});

