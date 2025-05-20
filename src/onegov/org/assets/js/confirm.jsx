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
    getInitialState: function() {
        return {
            hasScrolledToBottom: false
        };
    },

    componentDidMount: function() {
        // Check if the confirm-list exists and needs scroll tracking
        var confirmList = $(ReactDOM.findDOMNode(this)).find('.confirm-list');
        if (confirmList.length && confirmList.prop('scrollHeight') > confirmList.height()) {
            // Only activate scroll checking if there's enough content to scroll
            console.log(confirmList.prop('scrollHeight'), confirmList.height());
            confirmList.on('scroll', this.checkScrollPosition);

            // Set initial button state
            this.setState({ hasScrolledToBottom: false });

            // Apply styled class to indicate scrolling is required
            confirmList.addClass('requires-scroll');
        } else {
            // If there's not enough content to scroll, enable the button immediately
            this.setState({ hasScrolledToBottom: true });
        }
    },

    componentWillUnmount: function() {
        // Clean up scroll event listener
        var confirmList = $(ReactDOM.findDOMNode(this)).find('.confirm-list');
        confirmList.off('scroll', this.checkScrollPosition);
    },

    checkScrollPosition: function(e) {
        var list = e.currentTarget;

        // Check if scrolled to bottom (or very close to it)
        var isAtBottom =
            Math.abs((list.scrollHeight - list.scrollTop) - list.clientHeight) < 5;

        // Only update state if it changed
        if (isAtBottom !== this.state.hasScrolledToBottom) {
            this.setState({ hasScrolledToBottom: isAtBottom });
        }
    },

    render: function() {
        return (
            <div className="reveal-modal medium dialog" data-reveal role="dialog">
                <h2>{this.props.question}</h2>
                <p className="full-text-width">{this.props.extra}</p>
                {this.props.items &&
                <div className="confirm-list" style={{
                    border: this.state.hasScrolledToBottom ? '1px solid #ccc' : '1px solid #ffa500'
                }}>
                    {this.props.items}
                </div>
                }
                {!this.state.hasScrolledToBottom &&
                    <p className="scroll-hint full-text-width" style={{ color: '#ffa500', fontSize: '0.875rem' }}>
                        {this.props.scrollHint}
                    </p>
                }
                <a tabIndex="2" className="button secondary no">
                    {this.props.no}
                </a>
                <a tabIndex="1" className={this.state.hasScrolledToBottom ?
                    "button alert yes" : "button alert yes disabled"}
                   style={{ opacity: this.state.hasScrolledToBottom ? 1 : 0.6 }}>
                    {this.props.yes}
                </a>
            </div>
        );
    }
});

/*
    The confirmation, if no 'yes' button is supplied (to inform the user
    why some action can't be taken).
*/
var DenyConfirmation = React.createClass({
    render: function() {
        return (
            <div className="reveal-modal medium dialog" data-reveal role="dialog">
                <h2>{this.props.question}</h2>
                <p>{this.props.extra}</p>
                <a tabIndex="1" className="button secondary no">
                    {this.props.no}
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
var show_confirmation = function(question, yes, no, extra, items, scrollHint,
    handle_yes) {
    var el = $("<div class='confirm row'>");

    $('body').append(el);

    var confirm = null;

    if (_.isUndefined(yes)) {
        confirm = ReactDOM.render(
            <DenyConfirmation question={question} no={no} extra={extra} />,
            el.get(0)
        );
    } else {
        confirm = ReactDOM.render(
            <Confirmation
                question={question} yes={yes} no={no} extra={extra}
                items={items} scrollHint={scrollHint}
            />,
            el.get(0)
        );
    }
    var confirm_el = $(ReactDOM.findDOMNode(confirm));

    confirm_el.find('a.no').click(function() {
        confirm_el.foundation('reveal', 'close');
    });

    confirm_el.find('a.yes').click(function() {
        // Only call handle_yes if the button is not disabled
        if (!$(this).hasClass('disabled')) {
            handle_yes();
            confirm_el.foundation('reveal', 'close');
        }
    });

    confirm_el.foundation('reveal', 'open');
    confirm_el.focus();
};

/*
    Takes an element, an event ('click', or 'submit') and a handler.

    The handler will be injected at the front of the event queue, so it
    will get called first. If the handler returns false, the rest of the
    handlers will not be called. If true, they will be invoked in their
    original order (just like the browser does it).

*/
var intercept = function(element, event, handler) {
    var el = $(element);

    if (el.data('is-intercepted')) {
        return;
    }

    var existing_events = ($._data(element, 'events') || {})[event] || [];
    var existing_handlers = _.map(existing_events, _.property('handler'));

    var new_handler = function(e) {
        var that = $(this);

        var on_confirm = function() {

            // no associated handler => follow the href
            if (existing_handlers.length === 0 && typeof el.attr('href') !== 'undefined') {
                window.location = el.attr('href');
            }

            // associated handlers -> trigger them
            _.each(existing_handlers, function(existing_handler) {
                existing_handler.call(that, e);
            });
        };

        handler.call(that, e, on_confirm);
    };

    el.unbind(event);
    el[event](new_handler);
    el.data('is-intercepted', true);
};

// focus the yes button upon opening - modified to check if it's not disabled
$(document).on('opened.fndtn.reveal', '[data-reveal]', function() {
    var modal = $(this);
    _.defer(function() {
        var yesButton = modal.find('a.yes');
        if (!yesButton.hasClass('disabled')) {
            yesButton.focus();
        } else {
            // Focus on the scrollable area instead if the yes button is disabled
            modal.find('.confirm-list').focus();
        }
    });
});


function renderList(nodes) {
    if (!nodes || !nodes.length) return null;
    return (
        <ul>
            {nodes.map((node, idx) => (
                <li key={idx}>
                    {node.title}
                    {renderList(node.children)}
                </li>
            ))}
        </ul>
    );
}

// handles the click on the link (or other elements)
var handle_confirmation = function(e, on_confirm) {
    var question = $(this).data('confirm');
    var yes = $(this).data('confirm-yes');
    var no = $(this).data('confirm-no');
    var extra = $(this).data('confirm-extra');
    var items = $(this).data('confirm-items');
    items = renderList(items);
    var scrollHint = $(this).data('scroll-hint');
    console.log('scrollHint', scrollHint);

    show_confirmation(question, yes, no, extra, items, scrollHint, on_confirm);

    e.preventDefault();
};

// adds an enter key handler to jQuery
jQuery.fn.enter = function(callback) {
    if (!callback) {
        return;
    }

    $(this).keydown(function(e) {
        var ev = e || event;

        if (ev.keyCode === 13) {
            callback();
            return false;
        }

        return true;
    });
};

// sets up a confirmation link with the dialog
jQuery.fn.confirmation = function() {
    return this.each(function() {
        intercept(this, 'click', handle_confirmation);
    });
};

// hooks the targeted elements up
$(document).on('process-common-nodes', function(_e, elements) {
    $(elements).find('a.confirm').confirmation();
});

$(document).ready(function() {
    $('a.confirm').confirmation();
});
