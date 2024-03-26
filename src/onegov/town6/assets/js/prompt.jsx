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
var Prompt = createReactClass({

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
            <div>
                <h3>{this.props.question}</h3>
                <p>{this.props.info}</p>

                <input type="text" placeholder={this.props.placeholder} value={this.state.value} onChange={this.handleChange} />

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
    var el = $("<div class='prompt grid-x grid-padding-x'>");
    var dialog = $("<div class='reveal small dialog'>");
    dialog.attr('data-reveal', "")
    dialog.attr('id', Math.floor((Math.random() * 1000) + 1))
    dialog.appendTo(el)
    $('body').append(el);

    var prompt = ReactDOM.render(
        <Prompt
            question={options.question}
            info={options.info}
            ok={options.ok}
            cancel={options.cancel}
            value={options.value}
            placeholder={options.placeholder}
        />,
        dialog.get(0)
    );

    // In F6, we need to instantiate the plugins on the element
    dialog.foundation()

    dialog.find('a.cancel').click(function() {
        dropPrompt(dialog);
        return false;
    });

    dialog.find('a.ok').click(function() {
        options.success.call(options.target, prompt.state.value.trim());
        dropPrompt(dialog);
        return false;
    });

    dialog.find('input, a.ok').enter(function(e) {
        options.success.call(options.target, prompt.state.value.trim());
        dropPrompt(dialog);
        return false;
    });

    $('body').one('opened.fndtn.reveal', function() {
        dialog.find('input').focus().select();
    });

    dialog.foundation('open');
};

var dropPrompt = function(el) {
    el.foundation('close');
    el.remove();
};

// sets up a prompt
jQuery.fn.prompt = function() {
    /* eslint no-eval: 0 */

    $(this).click(function() {
        showPrompt({
            question: $(this).data('prompt'),
            info: $(this).data('prompt-info'),
            ok: $(this).data('prompt-ok'),
            cancel: $(this).data('prompt-cancel'),
            value: $(this).data('prompt-value'),
            success: eval($(this).data('prompt-success')),
            placeholder: $(this).data('prompt-placeholder'),
            target: $(this)
        });
    });
};

// hooks the targeted elements up
$(document).ready(function() {
    $('[data-prompt]').prompt();
});

$(document).on('process-common-nodes', function(_e, elements) {
    $(elements).find('[data-prompt]').prompt();
});
