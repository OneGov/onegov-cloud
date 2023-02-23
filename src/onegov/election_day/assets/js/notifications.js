var onWebsocketNotification = function(message, websocket) {
  if (message.event === 'refresh' && window.location.href.search(message.path) !== -1) {
    $(".page-refresh").show();
    websocket.close();
  }
}
