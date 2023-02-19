window.addEventListener("DOMContentLoaded", function() {
    if (typeof(WebsocketConfig) !== "undefined") {
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
            const data = JSON.parse(message.data)
            if (data.type === 'notification' && WebsocketConfig.onnotifcation) {
                WebsocketConfig.onnotifcation(data.message);
            }
        });
      } catch (error) {}
  }
});
