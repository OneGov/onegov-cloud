/*
    This module renders a timeline composed out of onegov chat messages.
    Supports different orders, pulling and pagination.
*/

/*
    Renders the result list
*/
var CSSTransitionGroup = React.addons.CSSTransitionGroup;

function isScrolledIntoView(el) {
    if (_.isUndefined(el)) {
        return false;
    }

    var top = el.getBoundingClientRect().top;
    var bottom = el.getBoundingClientRect().bottom;

    return (top >= 0) && (bottom <= window.innerHeight);
}

var TimelineMessages = React.createClass({
    getInitialState: function() {
        var messages = this.props.messages || [];

        // when getting the messages from the feed we add them at the top of
        // the messages list - to be consistent we make sure to accept messages
        // in the same order through the props - as they are ordered old -> new
        // we need to reverse here
        if (this.props.order === 'desc') {
            messages.reverse();
        }

        return {
            'messages': this.props.messages || []
        };
    },
    processMessageLinks: function() {
        var node = $(ReactDOM.findDOMNode(this));
        Intercooler.processNodes(node.get(0));

        var links = node.find('a.confirm');
        links.confirmation();
        setupRedirectAfter(links);
    },
    showNoMessagesHint: function() {
        var node = $(ReactDOM.findDOMNode(this));

        // if there's a .timeline-no-messages block on the same level as the
        // .timeline block, we'll show/hide if there are (no) messages
        if (this.state.messages.length === 0) {
            node.parent().parent().siblings('.timeline-no-messages').show();
        } else {
            node.parent().parent().siblings('.timeline-no-messages').hide();
        }
    },
    componentDidMount: function() {
        // we only do this on the initial load currently, as we hide all
        // links in the timeline - however we use the links in the ticket
        // view where all messages are loaded at once

        // when doing this for all messages we'll have to test if processing
        // the same links again and again works
        this.processMessageLinks();
        this.showNoMessagesHint();

        // automatically load more messages when scrolling down
        if (this.props.feed !== 'static') {
            var self = this;
            window.onscroll = _.throttle(function() {
                if (isScrolledIntoView(self.lastMessageElement())) {
                    if (self.props.order === 'desc') {
                        self.loadOlder();
                    } else {
                        self.loadNewer();
                    }
                }
            }, 1000);
        }
    },
    lastMessageElement: function() {
        return $(ReactDOM.findDOMNode(this)).find('li:last').get(0);
    },
    componentDidUpdate: function() {
        this.showNoMessagesHint();
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
                            <div className={(function() {
                                classes = ['message'];
                                classes.push('message-' + m.type);

                                if (showDate(ix)) {
                                    classes.push('first-of-day');
                                }

                                if (m.subtype !== "") {
                                    classes.push('message-' + m.type + '-' + m.subtype);
                                }

                                return classes.join(" ");
                            })()}
                                dangerouslySetInnerHTML={{__html: m.html}}
                            />
                        </li>
                    );
                    /* eslint-enable react/no-danger */
                })}
            </CSSTransitionGroup>
        );
    },
    load: function(direction) {
        var feed = new Url(this.props.feed);
        var self = this;
        var messages = this.state.messages;
        var queuefn = null;

        if (this.props.order === 'desc') {
            queuefn = direction === 'newer' && 'unshift' || 'push';
        } else {
            queuefn = direction === 'newer' && 'push' || 'unshift';
        }

        if (messages.length > 0) {
            if (direction === 'newer') {
                feed.query.load = 'older-first';

                if (this.props.order === 'desc') {
                    feed.query.newer_than = messages[0].id;
                } else {
                    feed.query.newer_than = messages[messages.length - 1].id;
                }
            }
            if (direction === 'older') {
                feed.query.load = 'newer-first';

                if (this.props.order === 'desc') {
                    delete feed.query.newer_than;
                    feed.query.older_than = messages[messages.length - 1].id;
                } else {
                    delete feed.query.newer_than;
                    feed.query.older_than = messages[0].id;
                }
            }
        }

        $.getJSON(feed.toString(), function(data) {
            var state = _.extend({}, self.state);

            for (var i = 0; i < data.messages.length; i++) {
                state.messages[queuefn](data.messages[i]);
            }

            self.setState(state);
        });
    },
    loadOlder: function() {
        this.load('older');
    },
    loadNewer: function() {
        this.load('newer');
    }
});

var Timeline = function(container) {
    var feed = container.data('feed');
    var messages = container.data('feed-data').messages || [];
    var order = container.data('feed-order') || 'desc';
    var interval = parseInt(container.data('feed-interval'), 10);
    var el = $('<div>');

    container.empty();
    container.append(el);
    container.timeline = ReactDOM.render(
        <TimelineMessages feed={feed} messages={messages} order={order} />, el.get(0)
    );

    if (feed && interval) {
        setInterval(container.timeline.loadNewer, interval * 1000);
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
