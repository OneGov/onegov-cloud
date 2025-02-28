
render_count = function(count) {
    return '(' + count + ')';
};

$('input[data-max-length],textarea[data-max-length]').each(function() {
    var $this = $(this);
    var counter_id = $this.attr('id') + '-counter';
    var max_length = $this.attr('data-max-length');
    var counter_element = document.createElement('SPAN');
    counter_element.innerHTML = render_count(max_length - this.value.length);
    counter_element.setAttribute("id", counter_id);
    this.before(counter_element);

    // Register event listener
    $this.keyup(function() {
        var el = $('#' + counter_id);
        el.html(render_count(max_length - this.value.length));
        if ((max_length - this.value.length) < 0) {
            el.css('color', '#FF0000');
        } else {
            el.removeAttr('style');
        }
    });
});

function handle_checkbox_disabled_until_start_date_set() {

    var publicationStart = $('#publication_start');
    var pushNotifications = $('#send_push_notifications_to_app');
    var newsInstances = $('#news_instances_selectable_for_publish').closest('.form-group'); // Adjust selector based on your markup

    console.log(newsInstances);
    console.log(pushNotifications)

    var togglePushNotification = function () {
        if (publicationStart.val()) {
            pushNotifications.prop('disabled', false);
        } else {
            pushNotifications.prop('disabled', true).prop('checked', false);
            newsInstances.hide(); // Hide dependent field
        }
    };

    var toggleNewsInstances = function () {
        if (pushNotifications.is(':checked')) {
            newsInstances.show();
        } else {
            newsInstances.hide();
        }
    };

    // Run immediately
    togglePushNotification();
    toggleNewsInstances();

    // Add event listeners
    publicationStart.on('input', function () {
        togglePushNotification();
        toggleNewsInstances();
    });

    pushNotifications.on('change', toggleNewsInstances);
}

$(document).ready(function() {
    handle_checkbox_disabled_until_start_date_set();
});
