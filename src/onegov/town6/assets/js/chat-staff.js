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
                message_area.style.display = 'flex'
                var chat_form = document.getElementById('chat-form')
                chat_form.style.display = 'block'
                newRequest.remove()
                noRequestText.style.display = 'block'

                const payload = JSON.stringify({
                    type: "accepted",
                    text: "Anfrage wurde angenommen",
                    channel: message.channel
                });

                websocket.send(payload);
            })
        } else if (message.type == 'message') {
            var self = false
            if (message.id == staffId) {
                self = true
            }
            createChatBubble(message.text, self)
        } else if (message.type == 'accepted') {
            var aceptedNotification = document.getElementById('accepted')
            aceptedNotification.style.display = 'flex'
        } else {
            createChatBubble(message.text, false)
        }
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


        document.getElementById("send").addEventListener("click", () => {

            const payload = JSON.stringify({
                type: 'message',
                text: chatWindow.value,
                user: staffName,
                id: staffId,
            });

            socket.send(payload);
            chatWindow.value = '';
        })
    }
});
