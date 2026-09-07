(function($) {
    $.Redactor.prototype.alphalist = function() {
        return {

            init: function() {
                var self = this;

                var button = this.button.addAfter('orderedlist', 'alphalist', this.lang.get('alphalist'));
                if (!button || !button.length) {
                    button = this.button.add('alphalist', this.lang.get('alphalist'));
                }

                self.$alphalistButton = button;

                button.on('click', function(e) {
                    e.preventDefault();
                    self.alphalist.toggle.call(self);
                });

                $(this.$editor).on('keyup mouseup', function() {
                    self.alphalist.updateButtonState.call(self);
                });
            },

            isAlphaList: function() {
                var current = this.selection.getBlock();
                if (!current) return false;
                var parent = current.parentNode;
                return $(parent).is('ol.alpha-list');
            },

            updateButtonState: function() {
                if (this.alphalist.isAlphaList.call(this)) {
                    this.$alphalistButton.addClass('redactor-act');
                } else {
                    this.$alphalistButton.removeClass('redactor-act');
                }

                var $olButton = this.button.get('orderedlist');
                if ($olButton) {
                    if (this.alphalist.isAlphaList.call(this)) {
                        $olButton.removeClass('redactor-act');
                    }
                }
            },

            focusEnd: function($element) {
                var $target = $element.is('ol, ul') ? $element.find('li').last() : $element;
                if (!$target.length) return;
                var range = document.createRange();
                var sel = window.getSelection();
                range.selectNodeContents($target[0]);
                range.collapse(false);
                sel.removeAllRanges();
                sel.addRange(range);
                this.alphalist.updateButtonState.call(this);
            },

            toggle: function() {
                var current = this.selection.getBlock();
                if (!current) return;

                var $editor = $(this.$editor);
                var selection = this.selection.get();
                var selectedBlocks = [];
                var parent = current.parentNode;

                if ($(parent).hasClass('alpha-list')) {
                    var $ol = $(parent);
                    var $items = $ol.find('li');
                    var blocks = [];
                    $items.each(function() {
                        blocks.push($('<p>').html($(this).html()));
                    });
                    $ol.replaceWith(blocks);
                    
                    this.$alphalistButton.removeClass('redactor-act');

                    this.alphalist.focusEnd.call(this, $(blocks[blocks.length - 1]));
                    return;
                }

                if (parent.nodeName === 'UL' || parent.nodeName === 'OL') {
                    if (!$(parent).hasClass('alpha-list')) {
                        var $newOl = $('<ol>').addClass('alpha-list').html($(parent).html());
                        $(parent).replaceWith($newOl);
                    }

                    this.alphalist.focusEnd.call(this, $newOl);
                    this.alphalist.updateButtonState.call(this);
                    return;
                }

                if (selection && !selection.isCollapsed) {
                    var range = selection.getRangeAt(0);
                    $editor.children().each(function() {
                        if (range.intersectsNode(this)) {
                            selectedBlocks.push(this);
                        }
                    });
                }

                if (selectedBlocks.length === 0) {
                    selectedBlocks.push(current);
                }

                var $ol = $('<ol>').addClass('alpha-list');
                $(selectedBlocks).each(function() {
                    var content = $(this).html();
                    $ol.append($('<li>').html(content));
                });

                $(selectedBlocks[0]).replaceWith($ol);
                for (var i = 1; i < selectedBlocks.length; i++) {
                    $(selectedBlocks[i]).remove();
                }
                this.alphalist.focusEnd.call(this, $ol);

                this.$alphalistButton.addClass('redactor-act');
                this.alphalist.updateButtonState.call(this);
            }
        };
    };
})(jQuery);