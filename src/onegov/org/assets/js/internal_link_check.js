$('[data-link-check]').each(function () {
    var check = $(this);
    var totalCounter = check.data('check-total') ? $(check.data('check-total')) : undefined
    var okCounter = check.data('check-ok') ? $(check.data('check-ok')) : undefined
    var nokCounter = check.data('check-nok') ? $(check.data('check-nok')) : undefined
    var errorCounter = check.data('check-error') ? $(check.data('check-error')) : undefined
    var errorMsgSelector = check.data('check-error-msg');
    var okClass = check.data('ok-class');
    var nokClass = check.data('nok-class');
    var statusSelector = check.data('status-selector');
    var removeDelay = check.data('remove-delay') || '1000'

    function addCount(obj, count) {
        if (!obj) return;
        var old = parseInt(obj.text());
        obj.text(old + parseInt(count));
    }

    function toggleClass(obj, selector, name) {
        if (selector && name) {
            obj.find(selector).toggleClass(name)
        }
    }

    function addErrorMsg(resp) {
        if (errorMsgSelector) {
            $(errorMsgSelector).text(resp.status || resp.statusText)
        }
    }

    check.find('[data-check-url]').each(function () {
        var self = $(this)
        $.ajax({
            type: "GET",
            async: false,
            url: self.data('check-url'),
            statusCode : {
                200: function () {
                    addCount(totalCounter, 1);
                    addCount(okCounter, 1);
                    toggleClass(self, statusSelector, okClass);
                    setTimeout(function () {
                        self.remove()
                    }, parseInt(removeDelay));
                }
            }
        }).fail(function(jqXHR) {
            if( jqXHR.status ) { addCount(nokCounter, 1); }
            else { addCount(errorCounter, 1); }
            toggleClass(self, statusSelector, nokClass);
            addCount(totalCounter, 1);
            addErrorMsg(jqXHR);
          })
    })
})

