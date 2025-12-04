$(document).ready(function() {
    $('.treeselect').each(function(_, select) {
        var container = $('<div>');
        $(select).hide().after(container);
        // eslint-disable-next-line no-unused-vars
        var treeselect = new Treeselect({
            parentHtmlContainer: container[0],
            options: $(select).data('choices'),
            value: $(select).val(),
            disabled: select.disabled,
            isSingleSelect: !select.multiple,
            saveScrollPosition: true,
            emptyText: $(select).data('no_results_text') || '',
            placeholder: $(select).data('placeholder') || '',
            showTags: true,
            searchable: true,
            clearable: true,
            isGroupedValue: true,
            inputCallback: function(value) {
                var values = [];
                for (var i = 0; i < value.length; i++) {
                    if (value[i].indexOf(':$:') > 0) {
                        var subvalues = value[i].split(':$:');
                        for (var j = 0; j < subvalues.length; j++) {
                            values[values.length] = subvalues[j];
                        }
                    } else {
                        values[values.length] = value[i];
                    }
                }
                $(select).val(values);
            },
            iconElements: {
                arrowUp: $('<i class="fa fa-caret-up">')[0],
                arrowDown: $('<i class="fa fa-caret-down">')[0],
                arrowRight: $('<i class="fa fa-caret-right">')[0],
                attention: $('<i class="fa fa-exclamation-triangle">')[0],
                clear: $('<i class="far fa-times-circle">')[0]
            }
        });
    });
});
