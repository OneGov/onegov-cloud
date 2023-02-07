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
            if (data.type === 'notification') {
                if (data.message.event === 'refresh') {
                    const path = data.message.path;
                    if (WebsocketConfig.onrefresh && path && window.location.pathname.search(path) !== -1) {
                        WebsocketConfig.onrefresh(data.message);
                    }
                }
            }
        });
      } catch (error) {}
  }
});
