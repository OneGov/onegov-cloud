$(document).ready(function () {
    // Handle click on the button to toggle the detail row
    $('a[id^="button-"]').on('click', function (e) {
        e.preventDefault();

        // Get the corresponding file number and detail row
        var id = $(this).attr('id').split('-').slice(1).join('-');
        var detailElement = $('#details-' + id);

        // Close all other detail elements
        $('*[id^="details-"]').not(detailElement).addClass('hidden');

        // Remove "down" class from all other chevron icons in the .files table
        $('i.fa-chevron-down').removeClass('down');

        // Toggle the visibility of the clicked detail element
        detailElement.toggleClass('hidden');

        // Add "down" class to the clicked chevron icon only if the row is now visible
        if (!detailElement.hasClass('hidden')) {
            $(this).find('i.fa-chevron-down').addClass('down');
        }
    });
});