var onWebsocketNotification = function(message) {
  if (message.event === 'browser-notification' && message.title && "Notification" in window) {
    if (Notification.permission === "granted") {
      new Notification(message.title);
    }
  }
}

$(document).ready(function() {
  if ("Notification" in window) {
    if (Notification.permission === "granted") {
      $('.ticket-notifications').addClass("granted");
      $('.ticket-notifications').removeClass("secondary");
    } else {
      $('.ticket-notifications').click(function() {
        Notification.requestPermission().then(function(permission){
          if (permission === "granted") {
            $('.ticket-notifications').addClass("granted");
            $('.ticket-notifications').removeClass("secondary");
          }
        })
      });
    }
  } else {
    $('.ticket-notifications').hide();
  }
});
