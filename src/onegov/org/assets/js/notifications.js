var onWebsocketNotification = function(message, _websocket) {
    if (message.event === 'browser-notification' && message.title && "Notification" in window) {
        if (Notification.permission === "granted") {
            // eslint-disable-next-line no-new
            new Notification(message.title, {tag: message.created});
        }
    }
};

$(document).ready(function() {
    if ("Notification" in window) {
        if (Notification.permission === "granted") {
            $('.ticket-notifications').addClass("granted");
            $('.ticket-notifications').removeClass("secondary");

            const endpoint = $('body').data('websocket-endpoint');
            const schema = $('body').data('websocket-schema');
            const channel = $('body').data('websocket-channel');
            if (endpoint && schema && channel) {
                openWebsocket(endpoint, schema, channel, onWebsocketNotification);
            }
        } else {
            $('.ticket-notifications').click(function() {
                Notification.requestPermission().then(function(permission) {
                    if (permission === "granted") {
                        window.location.reload();
                    }
                });
            });
        }
    } else {
        $('.ticket-notifications').hide();
    }
});
