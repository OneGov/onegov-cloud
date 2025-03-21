$(document).ready(function(){
    var categories = [];
    var hierarchy = [];
    $(".chosen-select option").each(function() {
        hierarchy.push($(this).val());
    });

    $(".chosen-select").chosen().change(function (event) {
        console.log('change');

        new_categories = $(event.target).val();
        
        var added_categories = new_categories.filter((e) => !categories.includes(e));
        console.log('added',added_categories);
        var removed_categories = categories.filter((e) => !new_categories.includes(e));
        console.log('removed', removed_categories);
        categories = new_categories;

        added_categories.forEach(function(added_category) {
            $(".chosen-select").trigger("chosen:updated")
            categories.push(added_category);
            if (added_category.startsWith('-')) {
                var parent_category = null;
                for (var i = hierarchy.indexOf(added_category) - 1; i >= 0; i--) {
                    if (!hierarchy[i].startsWith('-')) {
                        parent_category = hierarchy[i];
                        break;
                    }
                }
                if (parent_category) {
                    $(".chosen-select option[value='" + parent_category + "']").prop('selected', true).trigger("chosen:updated");
                }
            }
        });

        removed_categories.forEach(function(removed_category) {
            $(".chosen-select").trigger("chosen:updated")
            categories = categories.filter(function(value, index, arr){ return value != removed_category;});
            if (!removed_category.startsWith('-')) {
                var child_categories = [];
                for (var i = hierarchy.indexOf(removed_category) + 1; i < hierarchy.length; i++) {
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
        }
        );
    });
})
