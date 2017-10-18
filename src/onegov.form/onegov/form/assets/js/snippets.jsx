var FormSnippets = React.createClass({
    render: function() {
        var self = this;

        return (
            <div className="formcode-toolbar">
                <ToolbarElement label={this.props.labels.insert}>
                    {this.props.snippets.map(function(snippet, ix) {
                        return (
                            <FormSnippet
                                key={ix}
                                snippet={snippet}
                                required={self.props.labels.required}
                                optional={self.props.labels.optional}
                                target={self.props.target}
                            />
                        );
                    })}
                </ToolbarElement>
            </div>
        );
    }
});

var FormSnippet = React.createClass({
    insertSnippet: function(snippet) {
        var target = document.querySelector(this.props.target);
        target.value += '\n' + snippet;
    },
    handleRequired: function() {
        this.insertSnippet(
            this.props.snippet[0] + ' *= ' + this.props.snippet[1]
        );
    },
    handleOptional: function() {
        this.insertSnippet(
            this.props.snippet[0] + ' = ' + this.props.snippet[1]
        );
    },
    render: function() {
        var name = this.props.snippet[0];

        return (
            <div className="formcode-snippet">
                <span className="formcode-snippet-name">{name}</span>
                <span
                    className="formcode-snippet-required"
                    onClick={this.handleRequired}
                >
                    {this.props.required}
                </span>
                <span
                    className="formcode-snippet-optional"
                    onClick={this.handleOptional}
                >
                    {this.props.optional}
                </span>
            </div>
        );
    }
});

var ToolbarElement = React.createClass({
    getInitialState: function() {
        return {
            visible: false
        };
    },
    handleClick: function() {
        this.setState({visible: !this.state.visible});
    },
    render: function() {
        var classes = ['formcode-toolbar-element'];

        if (this.state.visible) {
            classes.push('formcode-toolbar-element-active');
        } else {
            classes.push('formcode-toolbar-element-inactive');
        }

        return (
            <div className={classes.join(' ')} onClick={this.handleClick}>
                <span>{this.props.label}</span>
                {this.state.visible && this.props.children}
            </div>
        );
    }
});

var initFormSnippets = function(container) {
    var xhr = new XMLHttpRequest();
    xhr.open('GET', container.getAttribute('data-source'));
    xhr.onload = function() {
        if (xhr.status === 200) {
            var data = JSON.parse(xhr.responseText);
            container.data = data;

            var el = document.createElement('div');
            container.appendChild(el);
            container.formsnippets = ReactDOM.render(
                <FormSnippets
                    labels={data.labels}
                    snippets={data.snippets}
                    target={container.getAttribute('data-target')}
                />,
                el
            );

        } else {
            console.log("XHR request failed with status " + xhr.status); // eslint-disable-line no-console
        }
    };
    xhr.send();
};

document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll('.formcode-snippets').forEach(initFormSnippets);
});
