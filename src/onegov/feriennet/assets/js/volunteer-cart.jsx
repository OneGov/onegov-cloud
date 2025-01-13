var VolunteerCart = React.createClass({
    getInitialState: function() {
        return {'items': []};
    },
    refresh: function() {
        var self = this;

        $.getJSON(this.props.cartURL, function(data) {
            self.setState({'items': data});
        });
    },
    remove: function(item) {
        var self = this;

        $.post(item.remove, function() {
            self.refresh();
        });
    },
    append: function(id, errorTarget) {
        var self = this;

        var url = this.props.cartActionURL
            .replace(/\/action/, '/add')
            .replace('target', id);

        $.post(url, function(data) {
            if (data.success) {
                self.refresh();
            } else {
                $(errorTarget).text(data.message).show();
            }
        });
    },
    render: function() {
        var self = this;

        var boundRemove = function(item) {
            return function(e) {
                self.remove(item);
                e.preventDefault();
            };
        };

        var volunteerCartList = (
            <div className="volunteer-cart">
                <div>{
                    self.state.items && self.state.items.map(function(item) {
                        return (
                            <div key={item.need_id} className="volunteer-cart-item">
                                <div className="cart-item-activity">
                                    {item.activity}
                                </div>
                                <div className="cart-item-need">
                                    {item.need}
                                </div>
                                <div className="cart-item-dates">
                                    <ul className="dense">{
                                        item.dates.map(function(date) {
                                            return (<li key={date}>{date}</li>);
                                        })
                                    }</ul>
                                </div>
                                <div className="cart-item-remove">
                                    <a href="#" onClick={boundRemove(item)}>{self.props.removeLabel}</a>
                                </div>
                            </div>
                        );
                    })
                }</div>
                <div>{
                    self.state.items.length === 0 && <p>
                        {self.props.emptyLabel}
                    </p>
                }</div>
                <div>{
                    self.state.items.length !== 0 && <a href={this.props.cartSubmitURL} className="button success">
                        {self.props.buttonLabel}
                    </a>
                }</div>
            </div>
        );

        if (self.props.isDropdown === 'False') {
            return volunteerCartList;
        } else {
            return (
                <div className="volunteer-cart-container">
                    <div className="volunteer-cart">
                        <button className={`button ${self.state.items.length === 0 ? 'hollow' : ''}`} type="button" data-toggle="my-list">
                            <i className="fa fa-chevron-down"></i>{self.props.listLabel} ({self.state.items.length})
                        </button>
                        <div className="dropdown-pane" id="my-list" data-dropdown data-auto-focus="true">
                            {volunteerCartList}
                        </div>
                    </div>
                </div>
            );
        }
    }
});

jQuery.fn.volunteerCart = function() {

    var container = $(this);
    if (!container.get(0)) return
    var el = container.get(0);

    var cart = ReactDOM.render(
        <VolunteerCart
            emptyLabel={container.attr('data-empty-label')}
            buttonLabel={container.attr('data-button-label')}
            removeLabel={container.attr('data-remove-label')}
            listLabel={container.attr('data-list-label')}
            isDropdown={container.attr('data-is-dropdown')}
            cartURL={container.attr('data-cart-url')}
            cartSubmitURL={container.attr('data-cart-submit-url')}
            cartActionURL={container.attr('data-cart-action-url')}
        />, el
    );

    cart.refresh();
    $(this).foundation();

    // only one cart is currently supported
    window.volunteerCart = cart;
};

$(document).ready(function() {
    $('.volunteer-cart-widget').volunteerCart();
});

Intercooler.ready((elt) => {
    $('.volunteer-cart-widget').volunteerCart();
});

