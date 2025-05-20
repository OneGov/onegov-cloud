var Confirmation = React.createClass({
    getInitialState: function() {
        return {
            hasScrolledToBottom: false
        };
    },

    componentDidMount: function() {
        // Use setTimeout to ensure the DOM has fully rendered
        setTimeout(() => {
            this.checkScrollableContent();
        }, 50);
    },

    componentWillUnmount: function() {
        // Clean up scroll event listener
        var confirmList = $(ReactDOM.findDOMNode(this)).find('.confirm-list');
        confirmList.off('scroll', this.checkScrollPosition);
    },

    checkScrollableContent: function() {
        // Check if the confirm-list exists and needs scroll tracking
        var confirmList = $(ReactDOM.findDOMNode(this)).find('.confirm-list');
        if (confirmList.length) {
            // Force a reflow/repaint to ensure correct measurements
            confirmList[0].getBoundingClientRect();

            var scrollHeight = confirmList.prop('scrollHeight');
            var clientHeight = confirmList.height();

            console.log("Measured dimensions:", scrollHeight, clientHeight);

            if (scrollHeight > clientHeight + 5) { // Add small buffer
                // Only activate scroll checking if there's enough content to scroll
                confirmList.on('scroll', this.checkScrollPosition);

                // Set initial button state
                this.setState({ hasScrolledToBottom: false });

                // Apply styled class to indicate scrolling is required
                confirmList.addClass('requires-scroll');
            } else {
                // If there's not enough content to scroll, enable the button immediately
                this.setState({ hasScrolledToBottom: true });
            }
        } else {
            // If no list exists, enable the button
            this.setState({ hasScrolledToBottom: true });
        }
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
                    border: this.state.hasScrolledToBottom ? '1px solid #ccc' : '1px solid #ffa500',
                    maxHeight: '200px',  // Set a fixed height to ensure scrolling works
                    overflowY: 'auto'    // Ensure overflow is set to auto
                }}>
                    {this.props.items}
                </div>
                }
                {!this.state.hasScrolledToBottom &&
                    <p className="scroll-hint full-text-width" style={{ color: '#ffa500', fontSize: '0.875rem' }}>
                        {this.props.scrollHint || "Please scroll to the bottom to continue"}
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