var locales = {
    de: {
        "Allocation": "Einteilung",
        "Reservation": "Reservation",
        "Reservations": "Termine",
        "Select allocations on the left to reserve them": "Wählen Sie die gewünschten Daten links aus",
        "Reserve": "Reservieren",
        "Remove": "Entfernen",
        "Whole day": "Ganztägig",
        "Yes": "Ja",
        "No": "Nein",
        "From": "Von",
        "Until": "Bis"
    }
};

var language = document.documentElement.getAttribute("lang").split('-')[0] || "en";

window.locale = function(text) {
    return locales[language] && locales[language][text] || text;
};
