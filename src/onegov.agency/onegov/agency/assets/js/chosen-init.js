$('.chosen-select').chosen({
    no_results_text: "Keine Ergebnisse gefunden:",
    placeholder_text_multiple: "Mehrere Optionen auswählen",
    placeholder_text_single: "Eine Option auswählen",
    search_contains: true,
    width: '100%'
}).on('change', function(event, parameters) {
    window.location.href = parameters.selected;
});
