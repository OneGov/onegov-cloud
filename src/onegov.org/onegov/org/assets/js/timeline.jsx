/*
    This module renders a timeline composed out of onegov chat messages.
    Supports different orders, pulling and pagination.
*/

/*
    Renders the result list
*/
var CSSTransitionGroup = React.addons.CSSTransitionGroup;

var TimelineMessages = React.createClass({
    getInitialState: function() {
        var messages = this.props.messages || [];

        // when getting the messages from the feed we add them at the top of
        // the messages list - to be consistent we make sure to accept messages
        // in the same order through the props - as they are ordered old -> new
        // we need to reverse here
        messages.reverse();

        return {
            'messages': this.props.messages || []
        };
    },
    componentDidMount: function() {
        var node = $(ReactDOM.findDOMNode(this));
        Intercooler.processNodes(node.get(0));

        var links = node.find('a.confirm');
        links.confirmation();
        setupRedirectAfter(links);

        // if there's a .timeline-no-messages block on the same level as the
        // .timeline block, we'll show/hide if there are (no) messages
        if (this.state.messages.length === 0) {
            node.parent().parent().siblings('.timeline-no-messages').show();
        } else {
            node.parent().parent().siblings('.timeline-no-messages').hide();
        }

        window.node = node;
    },
    render: function() {
        var messages = this.state.messages;
        var showDate = function(ix) {
            if (ix === 0) {
                return true;
            } else {
                return messages[ix - 1].date !== messages[ix].date;
            }
        };

        return (
            <CSSTransitionGroup
                component="ul"
                className="messages"
                transitionAppear={false}
                transitionLeave={false}
                transitionName="messages"
                transitionEnterTimeout={500}
                transitionLeaveTimeout={300}
            >
                {messages.map(function(m, ix) {
                    /* eslint-disable react/no-danger */
                    return (
                        <li key={m.id}>
                            {
                                showDate(ix) && <div className="date"><span>{m.date}</span></div>
                            }
                            <div className={'message message-' + m.type + ' ' + (showDate(ix) && 'first-of-day' || '')}
                                dangerouslySetInnerHTML={{__html: m.html}}
                            />
                        </li>
                    );
                    /* eslint-enable react/no-danger */
                })}
            </CSSTransitionGroup>
        );
    },
    update: function() {
        var feed = new Url(this.props.feed);
        var self = this;
        var messages = this.state.messages;
        var maxlength = 1000;

        if (messages.length > 0) {
            feed.query.newer_than = messages[0].id;
        }

        $.getJSON(feed.toString(), function(data) {
            var state = _.extend({}, self.state);

            for (var i = 0; i < data.messages.length; i++) {
                state.messages.unshift(data.messages[i]);
            }

            // remove messages at the bottom to reclaim memory
            if (messages.length > maxlength) {
                messages.splice(-1, messages.length - maxlength);
            }

            self.setState(state);
        });
    }
});

var Timeline = function(container) {
    var feed = container.data('feed');
    var messages = container.data('feed-data').messages || [];
    var interval = parseInt(container.data('feed-interval'), 10);
    var el = $('<div>');

    container.empty();
    container.append(el);
    container.timeline = ReactDOM.render(
        <TimelineMessages feed={feed} messages={messages} />, el.get(0)
    );

    if (feed && interval) {
        setInterval(container.timeline.update, interval * 1000);
    }
};

jQuery.fn.timeline = function() {
    return this.each(function() {
        Timeline($(this));
    });
};

$(document).ready(function() {
    $('div.timeline').timeline();
});
