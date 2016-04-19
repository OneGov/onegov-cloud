var locales = {
    de: {
        "Reservations": "Reservationen",
        "Select allocations on the right to reserve them": "Wählen Sie die gewünschten Daten rechts aus"
    }
};

var language = document.documentElement.getAttribute("lang").split('-')[0] || "en";

window.locale = function(text) {
    return locales[language] && locales[language][text] || text;
};
