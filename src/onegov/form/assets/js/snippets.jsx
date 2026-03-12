/*
    Renders formcode snippets served by onegov.form's FormApp in a menu.
    The menu is unstyled by default and is styled on a per-app basis.
*/

// Renders the formsnippets given by FormApp
var FormSnippets = React.createClass({
    render: function() {
        var self = this;

        return (
            <div className="formcode-toolbar">
                <ToggleButton icon="fa-plus-circle">
                    <div className="formcode-snippets">
                        {this.props.snippets.map(function(snippet, ix) {
                            var id = 'formcode-snippet-' + snippet[2].toLowerCase().replace(/[^a-z0-9]/g, '-');
                            return snippet[1] !== null && (
                                <FormSnippet
                                    key={ix}
                                    snippet={snippet}
                                    required={self.props.labels.required}
                                    optional={self.props.labels.optional}
                                    field_comment_example={self.props.labels.field_comment_example}
                                    target={self.props.target}
                                />
                            ) || (
                                <div key={ix} className="formcode-snippet-title" id={id}>
                                    {snippet[0]}
                                </div>
                            );
                        })}
                    </div>
                </ToggleButton>
            </div>
        );
    }
}); 

// Renders a single formsnippet and handles the insertion logic
var FormSnippet = React.createClass({
    insertSnippet: function(snippet) {
        formcodeUtils.updateTarget(this.props.target, snippet, this.props.snippet[0]);
    },
    getSnippet: function(required) {
        // comment are handled differently
        if (this.props.snippet[1] === '<<  >>') {
            return '<< ' + this.props.field_comment_example + ' >>';
        }
        // the title is the other thing that renders differently
        if (this.props.snippet[1] === '#') {
            return '# ' + this.props.snippet[0];
        }

        var separator = required && ' *= ' || ' = ';
        return this.props.snippet[0] + separator + this.props.snippet[1];
    },
    handleRequired: function() {
        this.insertSnippet(this.getSnippet(true));
    },
    handleOptional: function() {
        this.insertSnippet(this.getSnippet(false));
    },
    render: function() {
        var name = this.props.snippet[0];
        var id =  'formcode-snippet-' + this.props.snippet[2].toLowerCase().replace(/[^a-z0-9]/g, '-');

        return (
            <div className="formcode-snippet" id={id}>
                <div className="formcode-snippet-name" onClick={this.handleOptional}>{name}</div>
                {
                    (this.props.snippet[1] !== '#' && this.props.snippet[1] !== '<<  >>') &&
                    (
                        <div className="formcode-snippet-action">
                            <span
                                className="formcode-snippet-optional"
                                onClick={this.handleOptional}
                            >
                                {this.props.optional}
                            </span>
                            <span
                                className="formcode-snippet-required"
                                onClick={this.handleRequired}
                            >
                                {this.props.required}
                            </span>
                        </div>
                    ) || <div className="formcode-snippet-action" onClick={this.handleRequired} />
                }
            </div>
        );
    }
});

// loads the formcode snippets from the server and renders them
var initFormSnippets = function(container) {
    formcodeUtils.request('get', container.getAttribute('data-source'), function(data) {
        var el = container.appendChild(document.createElement('div'));

        ReactDOM.render(
            <FormSnippets
                labels={data.labels}
                snippets={data.snippets}
                target={container.getAttribute('data-target')}
            />,
            el
        );
    });
};
