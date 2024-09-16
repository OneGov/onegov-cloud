(function($) {
    let switchIntialized = false;

    $(document).on("tablesawcreate", function(_event, Tablesaw) {
        // Store and set the values of the column toggle checkboxes
        const checkboxSelector = '.tablesaw-columntoggle-popup .tablesaw-btn-group input[type="checkbox"]';
        $(checkboxSelector).each(function() {
            const key = Tablesaw.table.id + '-' + $(this).parent().text();
            if (key in localStorage) {
                const value = localStorage.getItem(key);
                if (value !== this.checked.toString()) {
                    this.checked = !this.checked;
                    $(this).trigger("change");
                }
            }
        });
        $(checkboxSelector).on("change", function(event) {
            const key = Tablesaw.table.id + '-' + $(event.target).parent().text();
            const value = event.target.checked.toString();
            localStorage.setItem(key, value);
        });

        // Store and set the values of the mode selector
        const switchSelector = '.tablesaw-modeswitch .tablesaw-btn-select select';
        $(switchSelector).each(function() {
            if (!switchIntialized) {
                switchIntialized = true;
                const key = Tablesaw.table.id + '-modeswitch';
                if (key in localStorage) {
                    const value = localStorage.getItem(key);
                    if (value !== this.value) {
                        this.value = value;
                        $(this).trigger("change");
                    }
                }
            }
        });
        $(switchSelector).on("change", function(event) {
            const key = Tablesaw.table.id + '-modeswitch';
            const value = event.target.value;
            localStorage.setItem(key, value);
        });

    });
})(jQuery);
