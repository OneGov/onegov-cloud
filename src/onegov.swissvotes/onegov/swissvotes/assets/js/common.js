// intercooler has the abilty to redirect depending on response headers
// we'd like for it to do the same with our own 'redirect-after' attribute
var setupRedirectAfter = function(elements) {
    elements.on('success.ic', function(_event, el) {
        var redirect_after = $(el).attr('redirect-after');
        if (!_.isUndefined(redirect_after)) {
            window.location = redirect_after;
        }

        return true;
    });
};


// Make the extended filters of the search collapsible and store the current
// state in the browser
var initSearchFilters = function() {
    var fieldsetLegend = $('#fieldset-other-filters legend');
    var key = 'fieldset-other-filters-hidden';

    fieldsetLegend.click(function() {
        var fieldset = $(this).parent('fieldset');
        localStorage.setItem(key, fieldset.hasClass('collapsed') ? 'visible' : 'hidden');
        fieldset.toggleClass('collapsed').children('.formfields').toggle();
    });

    if (key in localStorage) {
        var value = localStorage.getItem(key);
        if (value == 'hidden') {
            fieldsetLegend.click();
        }
    } else {
        fieldsetLegend.click();
    }
};

// sets up the given nodes with the functionality provided by common.js
// this is done at document.ready and can be repeated for out of band content
var processCommonNodes = function(elements, out_of_band) {
    var targets = $(elements);

    // intercooler integration (only done for dynamic content, and if
    // the nodes weren't already processed by intercooler)
    if (out_of_band !== false) {
        if (_.isUndefined(elements.data('ic-event-id'))) {
            Intercooler.processNodes(targets);
        }
    }

    // intercooler redirects
    setupRedirectAfter(targets.find('a'));

    // initialise zurb foundation (only works on the document level)
    $(document).foundation();

    // make the extended filters of the search collapsible
    initSearchFilters();

    // initalize the bar charts
    targets.find('.bar-chart').each(function(ix, el) {
        var dataurl = $(el).data('dataurl');
        $.ajax({url: dataurl}).done(function(data) {
            var chart = barChart({
                data: data,
                interactive: true
            })(el);
        });
    });

    // make the vote detail tables collapsible
    targets.find('table.collapsible thead').click(function() {
        $(this).parent('table').toggleClass('collapsed');
    });

    // set the language of the date picker
    jQuery.datetimepicker.setLocale(
        targets.find('html').attr('lang').split('-')[0]
    );

    // sort tables wishing to be sorted (when not using tablesaw)
    targets.find('table:not(.tablesaw).sortable').tablesorter();

    // send an event to allow optional scripts to hook themselves up
    // (we only do out of band updates since it's not guaranteed that these
    // extra scripts are already set up with the event at the initial call)
    if (out_of_band !== false) {
        $(document).trigger('process-common-nodes', elements);
    }

    // send clicks from certain blocks down to the first link
    targets.find('.click-through').click(function() {
        var link = $(this).find('a:first');
        var handlers = $._data(link[0]);

        if (handlers && handlers.click && handlers.click.length > 0) {
            link[0].click();
        } else if (link.data('elementAdded.ic') === true) {
            Intercooler.triggerRequest(link);
        } else {
            window.location = link.attr('href');
        }

        return false;
    });
};

// setup common nodes
processCommonNodes($(document), false);

// handle intercooler errors generically
$(document).ajaxError(function(_e, xhr, _settings, error) {
    if (xhr.status === 502) {
        showAlertMessage(locale(
            "The server could not be reached. Please try again."
        ));
    } else if (xhr.status === 503) {
        showAlertMessage(locale(
            "This site is currently undergoing scheduled maintenance, " +
            "please try again later."
        ));
    } else if (xhr.status === 500) {
        showAlertMessage(locale(
            "The server responded with an error. We have been informed " +
            "and will investigate the problem."
        ));
    } else if (500 <= xhr.status && xhr.status <= 599) {
        // a generic error messages is better than nothing
        showAlertMessage(error || xhr.statusText);
    }
});

// automatically setup redirect after / confirmation dialogs for
// things loaded by intercooler
Intercooler.ready(function(element) {
    var el = $(element);

    // the ready event is fired on the body as well -> no action required there
    if (el.is('body')) {
        return;
    }

    processCommonNodes(el, true);
});
