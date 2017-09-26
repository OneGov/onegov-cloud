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
        "Yes": "Ja",
        "Add Suggestion": "Vorschlag Hinzufügen",
        "Goto date": "Zu Datum springen",
        "Image": "Bild",
        "File": "Datei",
        "Internal Link": "Interner Link",
        "Upload": "Hochladen",
        "Select": "Auswählen"
    },
    fr: {
        "Allocation": "Allocation",
        "Add": "Ajouter",
        "Count": "Nombre",
        "Dates": "Dates",
        "From": "De",
        "No": "Non",
        "Remove": "Enlever",
        "Reserve": "Réserver",
        "Select allocations in the calendar to reserve them": "Sélectionnez les affectations dans le calendrier pour les réserver",
        "Until": "Jusqu'à",
        "Whole day": "Toute la journée",
        "Yes": "Oui",
        "Add Suggestion": "Ajouter une suggestion",
        "Goto date": " Aller à la date",
        "Image": "Image",
        "File": "Fichier",
        "Internal Link": "Lien interne",
        "Upload": "Télécharger",
        "Select": "Sélectionner"
    }
};

var language = document.documentElement.getAttribute("lang").split('-')[0] || "en";

window.locale = function(text) {
    return locales[language] && locales[language][text] || text;
};

window.locale.language = language;
