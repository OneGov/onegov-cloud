var locales = {
    de: {
        "Allocation": "Einteilung",
        "Add": "Hinzufügen",
        "Count": "Anzahl",
        "Dates": "Termine",
        "From": "Von",
        "No": "Nein",
        "Remove": "Entfernen",
        "Reserve": "Reservieren",
        "Select allocations in the calendar to reserve them": "Wählen Sie die gewünschten Termine im Kalender aus",
        "Until": "Bis",
        "Whole day": "Ganztägig",
        "Yes": "Ja"
    }
};

var language = document.documentElement.getAttribute("lang").split('-')[0] || "en";

window.locale = function(text) {
    return locales[language] && locales[language][text] || text;
};

window.locale.language = language;
