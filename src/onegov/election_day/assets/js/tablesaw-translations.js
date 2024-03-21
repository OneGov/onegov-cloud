const TablesawConfig = {};

switch (document.documentElement.getAttribute("lang")) {
    case "de-CH":
        TablesawConfig.i18n = {
            modeStack: "Gestapelt",
            modeToggle: "Auswahl",
            modeSwitchColumns: "Spalten",
            modeSwitchColumnsAbbreviated: "Spalten"
        };
        break;

    case "fr-CH":
        TablesawConfig.i18n = {
            modeStack: "Pile",
            modeToggle: "Levier",
            modeSwitchColumns: "Colonnes",
            modeSwitchColumnsAbbreviated: "Colonnes"
        };
        break;

    case "it-CH":
        TablesawConfig.i18n = {
            modeStack: "Catasta",
            modeToggle: "Attivato",
            modeSwitchColumns: "Colonne",
            modeSwitchColumnsAbbreviated: "Colonne"
        };
        break;

    case "rm-CH":
        TablesawConfig.i18n = {
            modeStack: "Mantunà",
            modeToggle: "Selecziun",
            modeSwitchColumns: "Colonnas",
            modeSwitchColumnsAbbreviated: "Colonnas"
        };
        break;

    default:
        break;
}
