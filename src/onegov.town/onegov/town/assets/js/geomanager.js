(function($)
{
    $.Redactor.prototype.geomanager = function()
    {
        return {
            getTemplate: function()
            {
                return String() +
                '<section id="redactor-modal-geomanager-insert">' +
                    '<iframe id="map-select" class="embedded-map" scrolling="no" src="http://govikon.onegov.dev/karte/46.801111/8.226667/8">&nbsp;</iframe>' +
                '</section>';
            },
            init: function()
            {
                var button = this.button.addAfter('image', 'geomanager', "Map");
                this.button.setAwesome('geomanager', 'fa-map-marker');
                this.button.addCallback(button, this.geomanager.show);
            },
            show: function()
            {
                this.modal.addTemplate('geomanager', this.geomanager.getTemplate());
                this.modal.load('geomanager', "Map", 700);
                this.modal.createCancelButton();

                var button = this.modal.createActionButton(this.lang.get('insert'));
                button.on('click', this.geomanager.insert);

                this.modal.show();

                $('#redactor-modal-geomanager-insert').focus();
            },
            insert: function()
            {
                var mapurl = $('#map-select')[0].contentWindow.location.href;
                var map = '<iframe class="embedded-map" scrolling="no" src="' + mapurl + '">&nbps;</iframe>';

                this.selection.restore();
                this.modal.close();

                var current = this.selection.getBlock() || this.selection.getCurrent();

                if (current) $(current).after(map);
                else
                {
                    this.insert.html(map, false);
                }

                this.code.sync();
            }
        };
    };
})(jQuery);
