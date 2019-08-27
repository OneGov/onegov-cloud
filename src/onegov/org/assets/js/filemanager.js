(function($)
{
    $.Redactor.prototype.filemanager = function()
    {
        return {
            init: function()
            {
                if (!this.opts.fileManagerJson) return;

                this.modal.addCallback('file', this.filemanager.load);
            },
            load: function()
            {
                var $modal = this.modal.getModal();

                this.modal.createTabber($modal);
                this.modal.addTab(1, window.locale("Upload"), 'active');
                this.modal.addTab(2, window.locale("Select"));

                $('#redactor-modal-file-upload-box').addClass('redactor-tab redactor-tab1');

                var $box = $('<div id="redactor-file-manager-box" class="redactor-tab redactor-tab2">').hide();
                $modal.append($box);


                $.ajax({
                  dataType: "json",
                  cache: false,
                  url: this.opts.fileManagerJson,
                  success: $.proxy(function(data)
                    {
                        var ul = $('<ul id="redactor-modal-list">');
                        $.each(data, $.proxy(function(key, val)
                        {
                            var a = $('<a href="#" title="' + val.title + '" rel="' + val.link + '" class="redactor-file-manager-link">' + val.title + '</a>');
                            var li = $('<li />');

                            a.on('click', $.proxy(this.filemanager.insert, this));

                            li.append(a);
                            ul.append(li);

                        }, this));

                        $('#redactor-file-manager-box').append(ul);


                    }, this)
                });

            },
            insert: function(e)
            {
                e.preventDefault();

                var $target = $(e.target).closest('.redactor-file-manager-link');

                this.file.insert('<a href="' + $target.attr('rel') + '">' + $target.attr('title') + '</a>');
            }
        };
    };
})(jQuery);