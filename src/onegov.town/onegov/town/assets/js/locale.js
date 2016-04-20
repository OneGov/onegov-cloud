var locales = {
    de: {
        "Allocation": "Einteilung",
        "Add": "Hinzufügen",
        "Count": "Anzahl",
        "Dates": "Daten",
        "From": "Von",
        "No": "Nein",
        "Remove": "Entfernen",
        "Reserve": "Reservieren",
        "Select allocations on the left to reserve them": "Wählen Sie die gewünschten Daten links aus",
        "Until": "Bis",
        "Whole day": "Ganztägig",
        "Yes": "Ja"
    }
};

var language = document.documentElement.getAttribute("lang").split('-')[0] || "en";

window.locale = function(text) {
    return locales[language] && locales[language][text] || text;
};
