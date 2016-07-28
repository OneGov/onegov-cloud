if (!RedactorPlugins) var RedactorPlugins = {};

(function($)
{
	RedactorPlugins.imagemanager = function()
	{
		return {
			init: function()
			{
				if (!this.opts.imageManagerJson) return;

				this.modal.addCallback('image', this.imagemanager.load);
			},
			load: function()
			{
				var $modal = this.modal.getModal();

				this.modal.createTabber($modal);
				this.modal.addTab(1, 'Hochladen', 'active');
				this.modal.addTab(2, 'Auswählen');

				$('#redactor-modal-image-droparea').addClass('redactor-tab redactor-tab1');

				var $box = $('<div id="redactor-image-manager-box" style="overflow: auto; height: 300px;" class="redactor-tab redactor-tab2">').hide();
				$modal.append($box);

				$.ajax({
				  dataType: "json",
				  cache: false,
				  url: this.opts.imageManagerJson,
				  success: $.proxy(function(data)
					{
						$.each(data, $.proxy(function(key, groups)
						{
							var group = $('<p style="margin: 1rem 0 0 0;">' + groups.group + '</p>');
							$('#redactor-image-manager-box').append(group);

							$.each(groups.images, $.proxy(function(key, val)
							{
								// title
								var thumbtitle = '';
								if (typeof val.title !== 'undefined') thumbtitle = val.title;

								var img = $('<img class="lazyload" data-src="' + val.thumb + '" rel="' + val.image + '" title="' + thumbtitle + '" style="max-width: 192px; max-height: 192px; cursor: pointer;" />');
								$('#redactor-image-manager-box').append(img);
								$(img).click($.proxy(this.imagemanager.insert, this));

							}, this));

						}, this));

						this.observe.images();

					}, this)
				});


			},
			insert: function(e)
			{
				var url = $(e.target).attr('rel');
				this.image.insert('<img src="' + url + '">');
			}
		};
	};
})(jQuery);
