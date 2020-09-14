function modifyScanJobForm () {
    var yearPattern = /\d+/;
    var labelOlder = $('#dispatch_tax_forms_older').parent().children().first();
    var labelLastYear = $('#dispatch_tax_forms_last_year').parent().children().first();
    var labelCurrentYear = $('#dispatch_tax_forms_current_year').parent().children().first();

    $('#dispatch_date').on('input', function () {
        var dispatchYear = this.value.split('-')[0];
        if (dispatchYear && dispatchYear.length === 4) {
            var year = parseInt(dispatchYear);
            labelCurrentYear.text(labelCurrentYear.text().replace(yearPattern, year));
            labelLastYear.text(labelLastYear.text().replace(yearPattern, year - 1));
            labelOlder.text(labelOlder.text().replace(yearPattern, year - 2));
        }
    })

}
$(document).ready(function () {
    modifyScanJobForm();
})

