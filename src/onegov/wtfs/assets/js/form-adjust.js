
var updateLabels = function (dispatchYear) {
    var input_ids = [
        '#dispatch_tax_forms_current_year',
        '#dispatch_tax_forms_last_year',
        '#dispatch_tax_forms_older',
        '#return_tax_forms_current_year',
        '#return_tax_forms_last_year',
        '#return_tax_forms_older',
        '#return_unscanned_tax_forms_current_year',
        '#return_unscanned_tax_forms_last_year',
        '#return_unscanned_tax_forms_older',
    ]
    var yearPattern = /\d+/;
    if (dispatchYear && dispatchYear.length === 4) {
        var year = parseInt(dispatchYear);
        var i;
        var replace_year;
        for (i = 0; i < input_ids.length; i++) {
            if (input_ids[i].includes('current_year')) {
                replace_year = year
            } else if (input_ids[i].includes('last_year')) {
                replace_year = year - 1
            } else {
                replace_year = year - 2
            }
            var label = $(input_ids[i]).parent().children().first()
            label.text(label.text().replace(yearPattern, replace_year))
        }
    }
}

var updateDispatchDates = function(dispatch_date, return_date) {
    $('#dispatch_date').val(dispatch_date);
    $('#return_date').val(return_date);
    updateLabels(dispatch_date.split('-')[0])
}

function modifyScanJobForm () {
    $('#dispatch_date').on('input', function () {
        var dispatchYear = this.value.split('-')[0];
        updateLabels(dispatchYear)
    })

}
$(document).ready(function () {
    modifyScanJobForm();
})

