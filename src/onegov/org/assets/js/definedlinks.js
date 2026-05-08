/*
    The official definedlinks.js plugin, slightly extended by including
    optgroups in the dropdown.
*/
(function($)
{
    $.Redactor.prototype.definedlinks = function()
    {
        return {
            init: function()
            {
                if (!this.opts.definedLinks) return;

                this.modal.addCallback('link', $.proxy(this.definedlinks.load, this));

            },
            load: function()
            {
                var placeholder = this.lang.get('link_select_page');
                var $select = $(
                    '<select id="redactor-defined-links" '
                    + 'data-placeholder="' + placeholder + '" />'
                );
                $('#redactor-modal-link-insert').prepend($select);

                this.definedlinks.storage = {};

                $.getJSON(this.opts.definedLinks, $.proxy(function(data)
                {
                    var grouped = _.groupBy(
                        data, function(d) { return d.group; }
                    );
                    var key = 0;

                    $select.append($('<option>').val('').html(''));

                    $.each(_.groupBy(data, 'group'), $.proxy(
                        function(group, links) {

                            var $optgroup = $(
                                '<optgroup />'
                            ).attr('label', group);
                            $select.append($optgroup);

                            $.each(links, $.proxy(function(ix, val) {
                                this.definedlinks.storage[key] = val;
                                $optgroup.append(
                                    $('<option>').val(key).html(val.name)
                                );
                                key += 1;
                            }, this));
                        }, this
                    ));

                    $select.prop('selectedIndex', 0);

                    $select.chosen({
                        allow_single_deselect: true,
                        search_contains: true,
                        width: '100%'
                    });

                    $select.on(
                        'change',
                        $.proxy(this.definedlinks.select, this)
                    );

                }, this));

            },
            select: function(e)
            {
                var key = $(e.target).val();
                var name = '', url = '';
                if (key !== '' && key !== null && key !== undefined)
                {
                    name = this.definedlinks.storage[key].name;
                    url = this.definedlinks.storage[key].url;
                }

                $('#redactor-link-url').val(url);
                $('#redactor-link-url-text').val(name);
            }
        };
    };
})(jQuery);