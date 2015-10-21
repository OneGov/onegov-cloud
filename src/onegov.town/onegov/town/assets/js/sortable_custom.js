/*
    This module scans the page for unordered lists which have the
    'data-sortable' set. Those that do are expected to also have a
    'data-sortable-url' set which should look like this:

    https://example.xxx/yyy/{subject_id}/{direction}/{target_id}

    This enables drag&drop sorting on the list. Each time an element is
    moved around, the url is called with the following variables replaced:

    * subject_id: the id of the item moved around
    * target_id: the id above which or below which the subject is moved
    * direction: the direction relative to the target ('above' or 'below')

    For example, this url would move id 1 below id 3:
    .../1/below/3

    The ids are taken from the list item's 'data-sortable-id' attribute.
*/

var on_move_element = function(list, element, new_index, old_index) {
    var siblings = $(list).children('li');

    if (siblings.length < 2) {
        return;
    }

    var target = new_index === 0 ? siblings[1] : siblings[new_index - 1];
    var direction = new_index === 0 ? 'above' : 'below';

    var url = decodeURIComponent($(list).data('sortable-url'))
        .replace('{subject_id}', $(element).data('sortable-id'))
        .replace('{target_id}', $(target).data('sortable-id'))
        .replace('{direction}', direction);

    $.ajax({type: "PUT", url: url})
        .done(function() {
            $(element).addClass('flash').addClass('success');
        })
        .fail(function() {
            undo_move_element(list, element, new_index, old_index);
            $(element).addClass('flash').addClass('failure');
        })
        .always(function() {
            setTimeout(function() {
                $(element)
                    .removeClass('flash')
                    .removeClass('success')
                    .removeClass('failure');
            }, 1000);
        });
};

var undo_move_element = function(list, element, new_index, old_index) {
    var siblings = $(list).children('li');

    if (old_index === 0) {
        $(element).insertBefore($(siblings[0]));
    } else {
        if (old_index <= new_index) {
            // was moved down
            $(element).insertAfter($(siblings[old_index - 1]));
        } else {
            // was moved up
            $(element).insertAfter($(siblings[old_index]));
        }
    }
};

var setup_sortable_list = function(list_element) {
    var sortable = Sortable.create(list_element, {
        onUpdate: function(event) {
            on_move_element(list_element, event.item, event.newIndex, event.oldIndex);
        }
    });

    $(list_element).children('li').each(function() {
        this.addEventListener('dragstart', function(event) {
            $(event.target).addClass('dragging');
        });
    });
};


$(document).ready(function() {
    $('ul[data-sortable]').each(function() {
        setup_sortable_list(this);
    });
});
