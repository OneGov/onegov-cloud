$(document).ready(function () {
    // Handle click on the button to toggle the detail row
    $('a[id^="button-"]').on('click', function (e) {
        e.preventDefault();

        // Get the corresponding file number and detail row
        var fileNumber = $(this).attr('id').split('-')[1];
        var detailRow = $('#details-' + fileNumber);

        // Close all other detail rows
        $('tr[id^="details-"]').not(detailRow).addClass('hidden');

        // Remove "down" class from all other chevron icons in the .files table
        $('.files i.fa-chevron-down').removeClass('down');

        // Toggle the visibility of the clicked detail row
        detailRow.toggleClass('hidden');

        // Add "down" class to the clicked chevron icon only if the row is now visible
        if (!detailRow.hasClass('hidden')) {
            $(this).find('i.fa-chevron-down').addClass('down');
        }
    });
});