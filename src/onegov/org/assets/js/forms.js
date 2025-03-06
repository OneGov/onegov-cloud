
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
    var newsInstances = $('#news_instances_selectable_for_publish').closest('.form-group');

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

function auto_select_topic_id_if_only_one_exists() {
    var pushNotificationsCheckbox = $('#send_push_notifications_to_app');
    var topicCheckboxes = $('input[name="push_notifications"]');

    // Function to check if only one topic exists and select it
    var autoSelectSingleTopic = function() {
        // Only proceed if push notifications checkbox is checked
        if (pushNotificationsCheckbox.is(':checked')) {
            // If there's only one topic checkbox
            if (topicCheckboxes.length === 1) {
                topicCheckboxes.prop('checked', true);
            }
        }
    };

    // Run when push notifications checkbox is changed
    pushNotificationsCheckbox.on('change', function() {
        if ($(this).is(':checked')) {
            autoSelectSingleTopic();
        }
    });
}


$(document).ready(function() {
    handle_checkbox_disabled_until_start_date_set();
    auto_select_topic_id_if_only_one_exists();
});
