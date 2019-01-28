(function( $ ) {
	var switchIntialized = false;

	$(document).on("tablesawcreate", function(e, Tablesaw){
		// Store and set the values of the column toggle checkboxes
		var checkboxSelector = '.tablesaw-columntoggle-popup .btn-group input[type="checkbox"]';
		Tablesaw.$toolbar.find(checkboxSelector).each(function(){
			var key = Tablesaw.table.id + '-' + $(this).parent().text();
			if (key in localStorage) {
				var value = localStorage.getItem(key);
				if (value != this.checked.toString()) {
					this.checked = !this.checked;
					$(this).trigger("change");
                }
			}
		});
		Tablesaw.$toolbar.find(checkboxSelector).on("change", function(e) {
			var key = Tablesaw.table.id + '-' + $(e.target).parent().text();
			var value = e.target.checked.toString();
			localStorage.setItem(key, value);
		});

		// Store and set the values of the mode selector
		var switchSelector = '.tablesaw-modeswitch .tablesaw-btn-select select';
		Tablesaw.$toolbar.find(switchSelector).each(function(){
			if (!switchIntialized) {
				switchIntialized = true;
				var key = Tablesaw.table.id + '-modeswitch';
				if (key in localStorage) {
					var value = localStorage.getItem(key);
					if (value != this.value) {
						this.value = value;
						$(this).trigger("change");
					}
				}
			}
		});
		Tablesaw.$toolbar.find(switchSelector).on("change", function(e) {
			var key = Tablesaw.table.id + '-modeswitch';
			var value = e.target.value;
			localStorage.setItem(key, value);
		});

	});
})( jQuery );
