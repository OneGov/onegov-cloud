var DropdownTreeSelect = ReactDropdownTreeSelect.default;

jQuery.fn.policySelector = function() {
    return this.each(function() {
        var select = $(this);
        var data = select.data('tree');
        var placeholderText = select.data('placehoder-text');
        var noMatchesText = select.data('no-matches-text');
        var onChange = function(currentNode, selectedNodes) {
            select.val(selectedNodes.map(function(item) {return item.value;}));
        };
        var wrapper = $('<div class="policy-selector-wrapper" />');

        wrapper.insertAfter(select.parents('label'));
        ReactDOM.render(
            <DropdownTreeSelect
                data={data}
                onChange={onChange}
                placeholderText={placeholderText}
                noMatchesText={noMatchesText}
                />,
            wrapper.get(0)
        );
        select.hide();
    });
};

$(document).ready(function() {
    $('.policy-selector').policySelector();
});
