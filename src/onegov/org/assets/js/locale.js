var locales = {
    de: {
        "Allocation": "Verfügbarkeit",
        "Add": "Hinzufügen",
        "Count": "Anzahl",
        "Dates": "Termine",
        "From": "Von",
        "No": "Nein",
        "Remove": "Entfernen",
        "Remove all": "Alle entfernen",
        "Reserve": "Reservieren",
        "Select one ore more allocations in the calendar to reserve them.": "Wählen Sie einen oder mehrere Termine im Kalender aus.",
        "Select allocations in the list to reserve them": "Wählen Sie die gewünschten Termine in der Liste aus",
        "Until": "Bis",
        "Whole day": "Ganztägig",
        "Yes": "Ja",
        "Add Suggestion": "Vorschlag hinzufügen",
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
        "Remove all": "Enlever tout",
        "Reserve": "Réserver",
        "Select one ore more allocations in the calendar to reserve them.": "Sélectionnez une ou plusieurs affectations dans le calendrier pour les réserver.",
        "Select allocations in the list to reserve them": "Sélectionnez les affectations dans la liste pour les réserver",
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
    },
    it: {
        "Allocation": "Allocazione",
        "Add": "Aggiungi",
        "Count": "Conta",
        "Dates": "Date",
        "From": "A partire dal",
        "No": "No",
        "Remove": "Rimuovi",
        "Remove all": "Rimuovi tutto",
        "Reserve": "Prenota",
        "Select one ore more allocations in the calendar to reserve them.": "Selezionare una o più allocazioni nel calendario per prenotarle.",
        "Select allocations in the list to reserve them": "Seleziona le allocazioni nell'elenco per prenotarle",
        "Until": "Fino a quando",
        "Whole day": "Giorno intero",
        "Yes": "Sì",
        "Add Suggestion": "Aggiungi suggerimento",
        "Goto date": "Vai alla data",
        "Image": "Immagine",
        "File": "File",
        "Internal Link": "Collegamento interno",
        "Upload": "Carica",
        "Select": "Seleziona",
        "This site is currently undergoing scheduled maintenance, please try again later.": "Questo sito è attualmente in fase di manutenzione programmata, riprova più tardi.",
        "The server responded with an error. We have been informed and will investigate the problem.": "Il server ha risposto con un errore. Siamo stati informati e indagheremo sul problema.",
        "The server could not be reached. Please try again.": "Impossibile raggiungere il server. Per favore riprova.",
        "The site could not be found.": "Impossibile trovare il sito.",
        "Access denied. Please log in before continuing.": "Accesso negato. Effettua il login prima di continuare."
    }
};

var language = document.documentElement.getAttribute("lang").split('-')[0] || "en";

window.locale = function(text) {
    return locales[language] && locales[language][text] || text;
};

window.locale.language = language;
