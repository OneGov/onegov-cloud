function handleRefreshEvent(path) {
    // Toggle refresh alerts
    if (window.location.pathname.search(path) !== -1) {
        const collection = document.getElementsByClassName("websockets-refresh");
        for (let i = 0; i < collection.length; i++) {
            collection[i].style.display = "block";
        }
    }
}


window.addEventListener("DOMContentLoaded", function() {
    if (WebsocketConfig) {
      try {
        const websocket = new WebSocket(WebsocketConfig.endpoint);
        websocket.addEventListener("open", function() {
          let payload = {
            type: "register",
            schema: WebsocketConfig.schema
          }
          websocket.send(JSON.stringify(payload));
        });
        websocket.addEventListener('message', function(message) {
            console.log('Message from server ', message.data);  // todo: remove me!
            const payload = JSON.parse(message.data)
            if (payload.type === 'notification') {
                if (payload.message.event === 'refresh') {
                    handleRefreshEvent(payload.message.path);
                }
            }
        });
      } catch (error) {}
  }
});
