(function($, BlockNote) {
    'use strict';

    if (!BlockNote) {
        if (window.console) {
            window.console.error('The BlockNote bundle could not be loaded.');
        }
        return;
    }

    $(function() {
        BlockNote.mountAll(document);
    });
})(jQuery, window.OneGovBlockNote);
