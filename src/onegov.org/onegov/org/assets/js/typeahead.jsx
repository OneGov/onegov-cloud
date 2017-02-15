/*
    This module will scan the page for forms which have the data-typehead="on"
    attribute. In these forms it expects to find the following attributes:

    * data-typeahead-source (on the form), link to the suggestion url which
      is called with a q parameter and which is expected to return a plain list
      of suggestions

    * data-typeahead-target (on the form), link to the search url which is
      called with a q parameter if a search is executed, an option lucky
      parameter is passed, if the first result should be opened straight away.

    * data-typeahead-subject is set on the element which should trigger
      the typeahead (that would be a text input element)

    * data-typeahead-spinner is set on the element which will show the
      spinner. The spinner is meant to be a button with a font awesome icon as
      value.

    * data-typeahead-container is set on the element which will contain the
      list of results.
*/

/*
    Renders the result list
*/
var TypeaheadList = React.createClass({
    getInitialState: function() {
        return {'active': null};
    },
    render: function() {
        var active = this.state.active;
        var results = this.props.results;
        var target = this.props.target;

        return (
            <ul>
                {results.map(function(result) {
                    return (
                        <li key={result} className={active === result ? 'active' : ''}>
                            <a href={target + '?q=' + result}>{result}</a>
                        </li>
                    );
                })}
            </ul>
        );
    },
    enter: function() {
        if (!this.state.active) {
            return false;
        }

        window.location = this.props.target + '?q=' + encodeURIComponent(this.state.active);
        return true;
    },
    right: function() {
        if (!this.state.active) {
            return false;
        }

        window.location = this.props.target + '?lucky&q=' + encodeURIComponent(this.state.active);
        return true;
    },
    up: function() {
        var ix = this.props.results.indexOf(this.state.active);
        if (ix === -1 || ix === 0) {
            this.setState({active: null});
        } else if (ix >= 1) {
            this.setState({active: this.props.results[ix - 1]});
        }
    },
    down: function() {
        var ix = this.props.results.indexOf(this.state.active);
        if (ix === -1) {
            ix = 0;
        } else if (ix < (this.props.results.length - 1)) {
            ix += 1;
        }

        this.setState({active: this.props.results[ix]});
    }
});

var TypeAhead = function(form) {
    var source = form.data('typeahead-source');
    var target = form.data('typeahead-target');
    var subject = form.find('[data-typeahead-subject]');
    var spinner = form.find('[data-typeahead-spinner]');
    var container = form.find('[data-typeahead-container]');
    var typeahead = null;

    var update_typeahead = function(results) {
        var el = $('<div>');
        container.empty();
        container.append(el);

        typeahead = ReactDOM.render(
            <TypeaheadList results={results} target={target} />, el.get(0)
        );
    };

    var update_suggestions = _.debounce(function(text) {
        if (text.length === 0) {
            update_typeahead([]);
            spinner.attr('class', 'fa fa-search');
            return;
        }

        var request = $.get(source + '?q=' + encodeURIComponent(text));

        request.always(function() {
            spinner.attr('class', 'fa fa-search');
        });
        request.success(function(data) {
            update_typeahead(data);
        });
    }, 100);

    $(document).on('keydown', function(event) {
        if (event.ctrlKey || event.metaKey || event.altKey) {
            return;
        }

        if (event.keyCode <= 48) {
            return;
        }

        if ($(':focus').is('a') || !$(':focus').length) {
            $(subject).val('');
            $(subject)[0].focus();
        }
    });

    $(subject).on('keydown', function(event) {
        // enter
        if (event.keyCode === 13) {
            if (typeahead !== null && typeahead.enter()) {
                event.preventDefault();
            }
        }
        // arrow up
        else if (event.keyCode === 38) {
            if (typeahead !== null && typeahead.up()) {
                event.preventDefault();
            }
        }
        // arrow down
        else if (event.keyCode === 40) {
            if (typeahead !== null && typeahead.down()) {
                event.preventDefault();
            }
        }
        // arrow right
        else if (event.keyCode === 39) {
            if (typeahead !== null && typeahead.right()) {
                event.preventDefault();
            }
        }
    });

    $(subject).on('keyup', function(event) {
        // actual characters or backspace
        if (event.keyCode >= 48 || event.keyCode === 8) {
            spinner.attr('class', 'fa fa-refresh fa-spin');
            update_suggestions($(this).val());
            event.preventDefault();
        }
    });
};

jQuery.fn.typeahead = function() {
    return this.each(function() {
        TypeAhead($(this));
    });
};

$(document).ready(function() {
    $('form[data-typeahead="on"]').typeahead();
});
