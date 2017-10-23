// Takes its children and wraps them in a toggleable element, which is a button
// that pops up a menu when clicked.

var ToggleButton = React.createClass({  // eslint-disable-line no-unused-vars
    getInitialState: function() {
        return {
            visible: false
        };
    },
    componentWillMount: function() {
        document.addEventListener('click', this.handleGlobalClick);
    },
    componentWillUnmount: function() {
        document.removeEventListener('click', this.handleGlobalClick);
    },
    handleGlobalClick: function(e) {
        if (this.state.visible) {
            if (!ReactDOM.findDOMNode(this).contains(e.target)) {
                this.setState({visible: false});
            }
        }
    },
    handleClick: function(e) {
        this.setState({visible: !this.state.visible});
        e.preventDefault();
    },
    render: function() {
        return (
            <div className="formcode-toolbar-element" onClick={this.handleClick}>
                <span><i className={'fa ' + this.props.icon} aria-hidden="true" /></span>
                {this.state.visible && this.props.children}
            </div>
        );
    }
});
