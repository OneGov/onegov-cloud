# Wahlen & Abstimmungen Webapplikation

## Einleitung

Am Abstimmungssonntag werden Resultate zu einzelnen Wahlen und Abstimmungen laufend publiziert. Bei der neuen "Wahlen & Abstimmungen" Webapplikation geschieht dies über ein Webinterface, das CSV oder Excel Dateien mit provisorischen oder definitiven Resultaten entgegennimmt.

Dieses Dokument beschreibt das Format dieser CSV/Excel Dateien.

## Format Spezifikation Wahlen

### Dateiformate

Als Dateiformate werden CSV, XLS oder XLSX Dateien akzeptiert, welche von den Wahlprogrammen "Wabsti Wahlen und Abstimmungen (VRSG)" oder "Wahlen (SESAM)" generiert werden.

#### SESAM

Das SESAM-Export-Format enthalten direkt alle benötigten Daten. Folgende Spalten werden ausgewertet und sollten vorhanden sein:

    'Anzahl Sitze'
    'Wahlkreis-Nr'
    'Stimmberechtigte'
    'Wahlzettel'
    'Ungültige Wahlzettel'
    'Leere Wahlzettel'
    'Leere Stimmen'
    'Kandidaten-Nr'
    'Name'
    'Vorname'
    'Anzahl Gemeinden'

Für Majorz-Wahlen zusätzlich:

    'Ungueltige Stimmen'
    'Stimmen'

Für Proporz-Wahlen hingegen zusätzlich:

    'Listen-Nr'
    'Partei-ID'
    'Parteibezeichnung'
    'HLV-Nr'
    'ULV-Nr'
    'Anzahl Sitze Liste'
    'Unveränderte Wahlzettel Liste'
    'Veränderte Wahlzettel Liste'
    'Kandidatenstimmen unveränderte Wahlzettel'
    'Zusatzstimmen unveränderte Wahlzettel'
    'Kandidatenstimmen veränderte Wahlzettel'
    'Zusatzstimmen veränderte Wahlzettel'
    'Gewählt'
    'Stimmen unveränderte Wahlzettel'
    'Stimmen veränderte Wahlzettel'
    'Stimmen Total aus Wahlzettel'

#### Wabsti (Majorz)

Folgende Spalten werden ausgewertet und sollten vorhanden sein:

    'AnzMandate'
    'BFS'
    'StimmBer'
    'StimmAbgegeben'
    'StimmLeer'
    'StimmUngueltig'
    'StimmGueltig'

Da das Datenformat keine Informationen über die gewählten Kandidaten liefert, müssen diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

**ID**

Die ID des Kandidaten.

**Name**

Der Familienname des Kandidaten.

**Vorname**

Der Vorname des Kandidaten.

#### Wabsti (Proporz)

Wabsti liefert die Daten in verschiedenen Dateien. Für die Resultate werden folgende Spalten ausgewertet und sollten vorhanden sein:

    'Einheit_BFS'
    'Liste_KandID'
    'Kand_Nachname'
    'Kand_Vorname'
    'Liste_ID'
    'Liste_Code'
    'Kand_StimmenTotal'
    'Liste_ParteistimmenTotal'

Die Datei mit den Statistiken zu den einzelnen Gemeinden sollte folgende Spalten enthalten:

    'Einheit_BFS'
    'StimBerTotal'
    'WZEingegangen'
    'WZLeer'
    'WZUngueltig'
    'StmWZVeraendertLeerAmtlLeer'

Die Datei mit den Listenverbindungen sollte folgende Spalten enthalten:

    'Liste'
    'LV'
    'LUV'

Da auch hier das Datenformat keine Informationen über die gewählten Kandidaten liefert, müssen diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

**ID**

Die ID des Kandidaten.

## Format Spezifikation Abstimmungen

### Dateiformat

Als Dateiformat werden CSV, XLS oder XLSX Dateien akzeptiert. Bei Excel Dateien wird entweder das erste Arbeitsblatt, oder sofern vorhanden das Arbeitsblatt mit dem Namen "Resultate" verwendet.

Die Dateien bestehen unabhängig vom verwendeten Dateiformat aus einer Kopfzeile und einer beliebigen Anzahl von Resultatzeilen. Die Kopfzeile enthält die Namen der Spalten und ist *zwingend erforderlich*.

Pro Abstimmungsvorlage besteht in der Regel eine CSV/Excel Datei. Beinhaltet die Abstimmung jedoch ein Gegenvorschlag und eine Stichfrage, dann müssen drei Dateien geliefert werden: Eine Datei mit den Resultaten der Abstimmung, eine Datei mit den Resultaten des Gegenvorschlags und eine Datei mit den Resultaten der Stichfrage.

### Felder

Jede Zeile enthält das Resultat einer einzelnen Gemeinde, sofern diese vollständig ausgezählt wurde.
Folgende Felder/Spalten werden dabei in der hier aufgelisteten Reihenfolge erwartet:

**Bezirk**

Der Bezirk in der sich die Gemeinde befindet. Ist die Gemeinde in keinem Bezirk, darf dieses Feld leer sein.

**BFS-Nummer**

Die BFS-Nummer der Gemeinde zum Zeitpunkt der Abstimmung.

**Gemeinde**

Der Name der Gemeinde.

**Ja Stimmen**

Die Anzahl Ja Stimmen zu der Abstimmung.
Ist der Text 'unbekannt' eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).

**Nein Stimmen**

Die Anzahl Nein Stimmen der Abstimmung.
Ist der Text 'unbekannt' eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).

**Stimmberechtigte**

Die Anzahl Stimmberechtigter.
Ist der Text 'unbekannt' eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).

**Leere Stimmzettel**

Die Anzahl leer eingelegter Stimmzettel.
Ist der Text 'unbekannt' eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).

**Ungültige Stimmzettel**

Die Anzahl ungültiger Stimmzettel.
Ist der Text 'unbekannt' eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).

### Vorlage

* XLS Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage.xls]()
* CSV Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage.csv]()
* XLSX Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage.xlsx]()

### Beispiel

«Schluss mit den Steuerprivilegien für Millionäre (Abschaffung der Pauschalbesteuerung)»

Resultate des Kanton Zug: [https://github.com/OneGov/onegov.election_day/blob/master/docs/steuerprivilegien.csv]()

| Bezirk | BFS-Nummer | Gemeinde    | Ja Stimmen | Nein Stimmen | Stimmberechtigte | Leere Stimmzettel | Ungültige Stimmzettel |
|--------|------------|-------------|------------|--------------|------------------|-------------------|-----------------------|
|        | 1711       | Zug         | 3515       | 6458         | 16914            | 123               | 123                   |
|        | 1706       | Oberägeri   | 575        | 1422         | 3639             | 123               | 123                   |
|        | 1709       | Unterägeri  | 901        | 1930         | 5325             | 123               | 123                   |
|        | 1704       | Menzingen   | 435        | 1126         | 2960             | 123               | 123                   |
|        | 1701       | Baar        | 2454       | 4967         | 13982            | 123               | 123                   |
|        | 1702       | Cham        | 1741       | 3525         | 9768             | 123               | 123                   |
|        | 1703       | Hünenberg   | 1063       | 2375         | 5925             | 123               | 123                   |
|        | 1708       | Steinhausen | 1127       | 2178         | 5993             | 123               | 123                   |
|        | 1707       | Risch       | 1008       | 2151         | 6115             | 123               | 123                   |
|        | 1710       | Walchwil    | 369        | 985          | 2057             | 123               | 123                   |
|        | 1705       | Neuheim     | 193        | 529          | 1299             | 123               | 123                   |
