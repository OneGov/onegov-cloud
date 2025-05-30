$(document).ready(function(){
    var categories = [];
    var hierarchy = [];
    $(".chosen-select[multiple] option").each(function() {
        hierarchy.push($(this).val());
    });

    $(".chosen-select[multiple]").change(function (event) {
        var new_categories = $(event.target).val();
        if (!new_categories) {
            new_categories = [];
        }
        var added_category = new_categories.filter((e) => !categories.includes(e));
        var removed_category = categories.filter((e) => !new_categories.includes(e));
        categories = new_categories;

        if (added_category.length > 0) {
            categories.push(added_category[0]);
            if (added_category[0].startsWith('-')) {
                var parent_category = null;
                for (var i = hierarchy.indexOf(added_category[0]) - 1; i >= 0; i--) {
                    if (!hierarchy[i].startsWith('-')) {
                        parent_category = hierarchy[i];
                        break;
                    }
                }
                if (parent_category) {
                    $(".chosen-select option[value='" + parent_category + "']").prop('selected', true).trigger("chosen:updated");
                    categories.push(parent_category);
                }
            }
        };

        if (removed_category.length > 0) {
            categories = categories.filter(function(value, index, arr){ return value != removed_category[0];});
            if (!removed_category[0].startsWith('-')) {
                var child_categories = [];
                for (var i = hierarchy.indexOf(removed_category[0]) + 1; i < hierarchy.length; i++) {
                    if (!hierarchy[i].startsWith('-')) {
                        break;
                    }
                    child_categories.push(hierarchy[i]);
                }
                child_categories.forEach(function(child_category) {
                    $(".chosen-select option[value='" + child_category + "']").prop('selected', false).trigger("chosen:updated");
                    categories = categories.filter(function(value, index, arr){ return value != child_category;});
                });
            }
        };

    });
});
