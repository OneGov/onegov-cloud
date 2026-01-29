/*
    Implements a prompt dialog that asks for a text value. Usage:

    showPrompt({
        question: 'Question',
        info': 'Additional information',
        ok: 'Ok-button text',
        cancel: 'Cancel-button text',
        value: 'Prefilled value',
        success': function(value) {
            // called when the user has confirmed the input;
        }
    });
*/

/*
    Renders the zurb foundation reveal model. Takes question, yes and no
    as options (those are the texts for the respective elements).
*/
var Prompt = React.createClass({

    getInitialState: function() {
        return {
            'value': (this.props.value && this.props.value.trim() || '')
        };
    },

    handleChange: function(event) {
        this.setState({value: event.target.value});
    },

    render: function() {
        return (
            <div
                className="reveal-modal medium dialog"
                data-reveal
                role="dialog"
            >
                <h2>{this.props.question}</h2>
                <p>{this.props.info}</p>

                <input
                    name={this.props.name}
                    type="text"
                    placeholder={this.props.placeholder}
                    value={this.state.value}
                    autoComplete="off"
                    onChange={this.handleChange}
                />

                <a className="button secondary cancel">
                    {this.props.cancel}
                </a>
                <a className="button alert ok">
                    {this.props.ok}
                </a>
            </div>
        );
    }
});

/*
    Actually shows the prompt and handles the clicks on it.

    When 'cancel' is clicked, the window closes.

    When 'ok' is clicked, the window closes and the success function
    is invoked.
*/
var showPrompt = function(options) {
    var el = $("<div class='prompt row'>");

    $('body').append(el);

    var defer_close = options.defer_close || false;

    var prompt = ReactDOM.render(
        <Prompt
            name={options.name || 'prompt'}
            question={options.question}
            info={options.info}
            ok={options.ok}
            cancel={options.cancel}
            value={options.value}
            placeholder={options.placeholder}
        />,
        el.get(0)
    );

    var prompt_el = $(ReactDOM.findDOMNode(prompt));

    prompt_el.find('a.cancel').click(function() {
        dropPrompt(prompt_el);
        return false;
    });

    prompt_el.find('a.ok').click(function() {
        options.success();
        if (!defer_close) {
            dropPrompt(prompt_el);
        }
        return false;
    });

    prompt_el.find('input, a.ok').enter(function(e) {
        options.success();
        if (!defer_close) {
            dropPrompt(prompt_el);
        }
        return false;
    });

    $('body').one('opened.fndtn.reveal', function() {
        prompt_el.find('input').focus().select();
    });

    prompt_el.foundation('reveal', 'open');

    return prompt_el;
};

var dropPrompt = function(el) {
    el.foundation('reveal', 'close');
    el.remove();
};

// sets up a prompt
jQuery.fn.prompt = function() {
    return this.each(function() {
        var that = $(this);
        intercept(this, 'click', function(e, on_submit) {
            var prompt_el = showPrompt({
                defer_close: true,
                question: $(this).data('prompt'),
                info: $(this).data('prompt-info'),
                ok: $(this).data('prompt-ok'),
                cancel: $(this).data('prompt-cancel'),
                name: $(this).data('prompt-name') || 'prompt',
                value: $(this).data('prompt-value'),
                placeholder: $(this).data('prompt-placeholder'),
                success: on_submit,
            });
            that.one('complete.ic', function() {
                dropPrompt(prompt_el);
            });
            e.preventDefault();
        });
    });
};

// hooks the targeted elements up
$(document).on('process-common-nodes', function(_e, elements) {
    $(elements).find('[data-prompt]').prompt();
});

$(document).ready(function() {
    $('[data-prompt]').prompt();
});
