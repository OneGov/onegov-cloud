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
    const customerName = chatArea.dataset.customerName;
    const chatWindow = document.getElementById("chat");

    function onWebsocketNotification(message, _websocket) {
        message = JSON.parse(message)
        if (message.type == 'message') {
            var self = false
            if (message.id == '') {
                self = true
            }
            createChatBubble(message.text, message.time, self)
        } else if (message.type == 'accepted') {
            var aceptedNotification = document.getElementById('accepted')
            aceptedNotification.style.display = 'flex'
            browserNotification(aceptedNotification.textContent)
        } else {
            console.log('unkown messaage type', message)
        }
    }

    function onWebsocketError(_event, websocket) {
        websocket.close();
    }

    function createChatBubble(message, time, self) {
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
        const timeText = document.createTextNode(time);
        const text = document.createTextNode(message);
        
        timeNode.appendChild(timeText);
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
            'customer_chat',
        );

        console.log('i know the customer:', customerName)

        document.getElementById("send").addEventListener("click", () => {
            now = new Date().toUTCString()

            const payload = JSON.stringify({
                type: "message",
                text: chatWindow.value,
                user: customerName,
                id: '',
                time: now,
            });

            console.log('im about to send ', payload)

            socket.send(payload);
            chatWindow.value = '';
        })
    }

});
