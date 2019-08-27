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
        "Select": "Auswählen",
        "This site is currently undergoing scheduled maintenance, please try again later.": "Die Webseite wird gerade planmässig gewartet. Bitte versuchen Sie es später noch einmal.",
        "The server responded with an error. We have been informed and will investigate the problem.": "Auf dem Server ist ein Fehler aufgetreten. Wir wurden informiert und werden das Problem analysieren.",
        "The server could not be reached. Please try again.": "Der Server konnte nicht erreicht werden. Bitte probieren Sie es noch einmal.",
        "The site could not be found.": "Die Seite wurde nicht gefunden.",
        "Access denied. Please log in before continuing.": "Zugriff verweigert. Bitte melden Sie sich an bevor Sie weiterfahren."
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
        "Select": "Sélectionner",
        "This site is currently undergoing scheduled maintenance, please try again later.": "Le site est actuellement l'objet d'une maintenance programmée, veuillez réessayer plus tard.",
        "The server responded with an error. We have been informed and will investigate the problem.": "Le serveur a répondu par une erreur. Nous en avons été informés et nous étudierons le problème.",
        "The server could not be reached. Please try again.": "Le serveur n'a pas pu être joint. Veuillez réessayer.",
        "The site could not be found.": "Impossible de trouver le site.",
        "Access denied. Please log in before continuing.": "Accès refusé. Veuillez vous connecter avant de continuer."
    }
};

var language = document.documentElement.getAttribute("lang").split('-')[0] || "en";

window.locale = function(text) {
    return locales[language] && locales[language][text] || text;
};

window.locale.language = language;
