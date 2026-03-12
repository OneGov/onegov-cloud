/*
    This module will scan the page for forms which have the data-typehead="on"
    attribute. In these forms it expects to find the following attributes:

    * data-typeahead-source (on the form), link to the suggestion url which
      is called with a q parameter and which is expected to return a plain list
      of suggestions

    * data-typeahead-target (on the form), link to the search url which is
      called with a q parameter if a search is executed, an option lucky
      parameter is passed, if the first result should be opened straight away.

    * data-typeahead-filter-params (on the form), an optional array of extra
      form field names that should be included in the searchUrl as query
      params.

    * data-typeahead-subject is set on the element which should trigger
      the typeahead (that would be a text input element)

    * data-typeahead-container is set on the element which will contain the
      list of results.
*/

var getSearchUrl = function(target, query, lucky) {
    var url = new URL(target);
    url.searchParams.delete('page');
    url.searchParams.set('q', query);
    if (lucky) {
        url.searchParams.set('lucky', '1');
    }
    return url.toString();
};

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
                            <a href={getSearchUrl(target, result)}>{result}</a>
                        </li>
                    );
                })}
                <li className="dots"><button type="submit">…</button></li>
            </ul>
        );
    },
    enter: function() {
        if (!this.state.active) {
            return false;
        }

        window.location = getSearchUrl(this.props.target, this.state.active);
        return true;
    },
    right: function() {
        if (!this.state.active) {
            return false;
        }

        window.location = getSearchUrl(this.props.target, this.state.active, true);
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
    var filter_params = form.data('typeahead-filter-params') || [];
    var subject = form.find('[data-typeahead-subject]');
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
            return;
        }
        $.get(getSearchUrl(source, text), function(data) {
            update_typeahead(data);
        });
    }, 100);

    // eslint-disable-next-line complexity
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
            update_suggestions($(this).val());
            event.preventDefault();
        }
    });

    if (filter_params.length > 0) {
        form.on('change', function() {
            var source_url = new URL(source);
            var target_url = new URL(target);
            // clear filter params
            _.each(filter_params, function(field_name) {
                source_url.searchParams.delete(field_name);
                target_url.searchParams.delete(field_name);
            });
            // repopulate with form values
            _.each(form.serializeArray(), function(data) {
                if (_.contains(filter_params, data.name)) {
                    source_url.searchParams.append(data.name, data.value);
                    target_url.searchParams.append(data.name, data.value);
                }
            });
            source = source_url.toString();
            target = target_url.toString();
            if (typeahead !== null) {
                update_typeahead(typeahead.props.results);
            }
        });
    }
};

jQuery.fn.typeahead = function() {
    return this.each(function() {
        TypeAhead($(this));
    });
};

$(document).ready(function() {
    $('form[data-typeahead="on"]').typeahead();
});
