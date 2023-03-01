var onWebsocketNotification = function(message, websocket) {
  if (message.event === 'refresh' && window.location.href.search(message.path) !== -1) {
    $(".page-refresh").show();
    websocket.close();
  }
}

$(document).ready(function() {
  const endpoint = $('body').data('websocket-endpoint');
  const schema = $('body').data('websocket-schema');
  if (endpoint && schema) {
    openWebsocket(endpoint, schema, null, onWebsocketNotification);
  }
});
