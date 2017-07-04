/*
    This module renders a timeline composed out of onegov chat messages.
    Supports different orders, pulling and pagination.
*/

/*
    Renders the result list
*/
var TimelineMessages = React.createClass({
    getInitialState: function() {
        return {
            'messages': []
        };
    },
    render: function() {
        var messages = this.state.messages;
        return (
            <ul>
                {messages.map(function(m) {
                    /* eslint-disable react/no-danger */
                    return (
                        <li key={m.id} className={'message message-' + m.type}>
                            <div dangerouslySetInnerHTML={{__html: m.html}} />
                        </li>
                    );
                })}
            </ul>
        );
    },
    update: function() {
        var feed = new Url(this.props.feed);
        var self = this;
        var messages = this.state.messages;

        if (messages.length > 0) {
            feed.query.newer_than = messages[0].id;
        }

        $.getJSON(feed.toString(), function(data) {
            var state = _.extend({}, self.state);

            for (var i = 0; i < data.messages.length; i++) {
                state.messages.unshift(data.messages[i]);
            }

            self.setState(state);
        });
    }
});

var Timeline = function(container) {
    var feed = container.data('feed');
    var poll_interval = parseInt(container.data('poll-interval'), 10);
    var el = $('<div>');

    container.empty();
    container.append(el);
    container.timeline = ReactDOM.render(
        <TimelineMessages feed={feed} />, el.get(0)
    );
    container.timeline.update();

    setInterval(container.timeline.update, poll_interval * 1000);
};

jQuery.fn.timeline = function() {
    return this.each(function() {
        Timeline($(this));
    });
};

$(document).ready(function() {
    $('.timeline').timeline();
});
