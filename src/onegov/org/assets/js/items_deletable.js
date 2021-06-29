$('[data-items-deletable]').each(function () {
    var self = $(this);
    var trigger = $(self.data('trigger'));
    var selectAll = $(self.data('select-all'));
    var removeItem = self.data('remove');
    var seletableItems = self.find('[data-url]');
    var checkboxSelector = self.data('checkbox-selector')
    var requestMethod = self.data('request-method') || 'DELETE'

    var checked = function(item, new_state) {
        var el = item.find(checkboxSelector);
        if(new_state === undefined) {
            return el.prop('checked')
        }
        el.prop('checked', new_state)
    }

    var toggleAll = function (state) {
        seletableItems.each(function () {
            checked($(this), state)
        })
    }

    var updateReady = function (ready) {
        if(ready) {
            trigger.addClass('ready');
        } else {
            trigger.removeClass('ready');
        }
    }

    var anyOther = function(skip_ix) {
        var isChecked = false
        $.each(seletableItems, function (ix, item) {
            if(skip_ix !== ix && !isChecked && checked($(item))) {
                isChecked = true
            }
        })
        return isChecked
    }

    selectAll.on('click', function () {
        var state = $(this).prop('checked');
        updateReady(state);
        toggleAll(state);
    });


    $.each(seletableItems, function (ix, item) {
        $(item).on('click', function () {
            updateReady((checked($(this)) || anyOther(ix)));
        });
    })

    var callforDeletion = function(item, onSuccess){
        $.ajax({
            type: requestMethod,
            url: item.data('url'),
            statusCode : {
                200: function (resp) {
                    onSuccess(resp, item);
                }
            }
        }).fail(function(jqXHR) {
            console.log(jqXHR.statusMessage);
        })
    }

    trigger.on('click', function () {

        var onSuccess = function (resp, item){
            console.log(resp);
            if(removeItem) item.remove();
        }

        seletableItems.each(function () {
            var el = $(this);
            if (!checked(el)) return
            callforDeletion(el, onSuccess);
        })
    })
})