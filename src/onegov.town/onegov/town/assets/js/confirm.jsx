/*
    This module will scan the page for links, buttons and forms that have
    a data-confirm attribute (*). It will then intercept all clicks/submits
    on these elements and show a zurb foundation based modal with the
    data-confirm text above yes/no buttons.

    * Note that currently, only links are actually implemented.

    The click will then only be bubbled up if the yes button was clicked.

    A link that wants to use the confirmation dialog must be written like this:

    <a class="confirm"
       data-confirm="Do you really want to?"
       data-confirm-yes="Yes I do"
       data-confirm-no="Cancel"
       i18n:attributes="data-confirm;data-confirm-yes;data-confirm-no">Link</a>
*/

/* 
    Renders the zurb foundation reveal model. Takes question, yes and no
    as options (those are the texts for the respective elements).
*/
var Confirmation = React.createClass({
    render: function() {
        return (
            <div className="reveal-modal medium confirm-modal" data-reveal role="dialog">
                <h2>{this.props.question}</h2>
                <a tabIndex="1" className="button secondary no">
                    {this.props.no}
                </a>
                <a tabIndex="1" className="button alert yes">
                    {this.props.yes}
                </a>
            </div>
        );
    }
});

/*
    Actually shows the confirmation and handles the clicks on it.
    
    When 'no' is clicked, the window closes.

    When 'yes' is clicked, the window closes and the handle_yes function
    is invoked.
*/
var show_confirmation = function(question, yes, no, handle_yes) {
    var id = _.random(0, 65536);
    var el = $("<div class='confirm row'>");

    $('body').append(el);

    var confirm = React.render(
        <Confirmation question={question} yes={yes} no={no} />,
        el.get(0)
    );
    var confirm_el = $(confirm.getDOMNode());

    confirm_el.find('a.no').click(function() {
        confirm_el.foundation('reveal', 'close');
    });
    confirm_el.find('a.yes').click(function() {
        handle_yes();
        confirm_el.foundation('reveal', 'close');
    });
    confirm_el.find('a.yes').click(handle_yes);

    confirm_el.foundation('reveal', 'open');
};

/*
    Takes an element, an event ('click', or 'submit') and a handler.

    The handler will be injected at the front of the event queue, so it
    will get called first. If the handler returns false, the rest of the
    handlers will not be called. If true, they will be invoked in their
    original order (just like the browser does it).

*/
var intercept = function(element, event, handler) {
    var existing_events = $._data(element, 'events')[event];
    var existing_handlers = _.map(existing_events, _.property('handler'));

    var new_handler = function(e) {
        var that = $(this);

        var on_confirm = function() {
            _.each(existing_handlers, function(existing_handler) {
                existing_handler.call(that, e);
            });
        };

        handler.call(that, e, on_confirm);
    };

    $(element).unbind(event);
    $(element)[event](new_handler);
};

// remove the div when the dialog closes
$(document).on('closed.fndtn.reveal', '[data-reveal]', function () {
    if ($(this).parent().hasClass('confirm')) {
        $(this).parent().remove();
    }
});

// handles the click on the link (or other elements)
var handle_action = function(e, on_confirm) {
    var question = $(this).data('confirm');
    var yes = $(this).data('confirm-yes');
    var no = $(this).data('confirm-no');

    show_confirmation(question, yes, no, on_confirm);
};

// hooks the targeted elements up
$(document).ready(function() {
    _.each($('a.confirm'), function(el) {
        intercept(el, 'click', handle_action);
    });
});
