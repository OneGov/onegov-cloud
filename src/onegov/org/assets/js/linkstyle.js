/*
    Extends the link dialog of the editor with a style, which shows the link
    as a button (call to action): <a class="button cta" href="...">Apply</a>

    The classes are restricted by our html sanitizer, see
    onegov.core.html.SANE_LINK_CLASSES.
*/
(function($) {
    var STYLES = {
        '': '',
        'primary': 'button cta',
        'secondary': 'button cta secondary'
    };
    var STYLE_CLASSES = 'button cta secondary';

    $.Redactor.prototype.linkstyle = function() {
        return {
            init: function() {
                var show = this.link.show;
                var set = this.link.set;

                this.link.show = $.proxy(function(e) {
                    show(e);
                    this.linkstyle.addField();
                }, this);

                this.link.set = $.proxy(function(text, link, target) {
                    // the field is gone once the modal closes
                    var style = $('#redactor-link-style').val() || '';
                    var $existing = this.link.$node;

                    set(text, link, target);
                    this.linkstyle.apply($existing, link, text, style);
                }, this);
            },
            addField: function() {
                var $select = $('<select id="redactor-link-style">');
                $select.append($('<option value="">').text(window.locale('Text link')));
                $select.append($('<option value="primary">').text(window.locale('Primary button')));
                $select.append($('<option value="secondary">').text(window.locale('Secondary button')));

                var $link = this.link.$node;
                if ($link && $link.hasClass('cta')) {
                    $select.val($link.hasClass('secondary') ? 'secondary' : 'primary');
                }

                $('#redactor-modal-link-insert').append(
                    $('<label for="redactor-link-style">').text(window.locale('Style')),
                    $select
                );
            },
            apply: function($existing, url, text, style) {
                var $link = $existing && $existing.length ? $existing : $();

                // a new link: redactor selects it after inserting it
                if (!$link.length) {
                    $link = $(this.selection.getCurrent()).closest('a', this.$editor[0]);
                }
                if (!$link.length) {
                    $link = this.$editor.find('a').filter(function() {
                        return $(this).attr('href') === url;
                    }).last();
                }
                if (!$link.length) {
                    return;
                }

                // NOTE: Safari uses the url as text of new links, if no text
                //       was selected, redactor doesn't correct that
                text = $.trim((text || '').replace(/<|>/g, ''));
                if (!$existing && text && $link.text() !== text) {
                    $link.text(text);
                }

                $link.removeClass(STYLE_CLASSES).addClass(STYLES[style] || '');
                if (!$link.attr('class')) {
                    $link.removeAttr('class');
                }

                this.code.sync();
            }
        };
    };
})(jQuery);
