# Wahlen & Abstimmungen Webapplikation

## Einleitung

Am Abstimmungssonntag werden Resultate zu einzelnen Wahlen und Abstimmungen laufend publiziert. Bei der neuen "Wahlen & Abstimmungen" Webapplikation geschieht dies über ein Webinterface, das CSV oder Excel Dateien mit provisorischen oder definitiven Resultaten entgegennimmt.

Dieses Dokument beschreibt das Format dieser CSV/Excel Dateien.

## Format Spezifikation Wahlen

### Dateiformate

Als Dateiformate werden CSV, XLS oder XLSX Dateien akzeptiert, welche von den Wahlprogrammen "Wabsti Wahlen und Abstimmungen (VRSG)", "Wahlen (SESAM)" oder der Webapplikation selbst generiert werden. Falls eine Tabelle von Hand erstellt werden soll, ist das Nachbilden des eigene oder des SESAM-Formats einfacher.

#### SESAM

##### Majorz-Wahl

Das SESAM-Export-Format enthält direkt alle benötigten Daten. Es gibt pro Kandidat und Gemeinde eine Zeile. Folgende Spalten werden ausgewertet und sollten mindestens vorhanden sein:

* Anzahl Sitze
* Wahlkreis-Nr
* Stimmberechtigte
* Wahlzettel
* Ungültige Wahlzettel
* Leere Wahlzettel
* Leere Stimmen
* Kandidaten-Nr
* Gewaehlt
* Name
* Vorname
* Anzahl Gemeinden
* Ungueltige Stimmen
* Stimmen

Vorlage:

* XLS Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_sesam_majorz.xls]()
* CSV Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_sesam_majorz.csv]()
* XLSX Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_sesam_majorz.xlsx]()

##### Proporz-Wahl

Das SESAM-Export-Format enthält direkt alle benötigten Daten. Es gibt pro Kandidat und Gemeinde eine Zeile. Folgende Spalten werden ausgewertet und sollten mindestens vorhanden sein:

* Anzahl Sitze
* Wahlkreis-Nr
* Stimmberechtigte
* Wahlzettel
* Ungültige Wahlzettel
* Leere Wahlzettel
* Leere Stimmen
* Listen-Nr
* Partei-ID
* Parteibezeichnung
* HLV-Nr
* ULV-Nr
* Anzahl Sitze Liste
* Unveränderte Wahlzettel Liste
* Veränderte Wahlzettel Liste
* Kandidatenstimmen unveränderte Wahlzettel
* Zusatzstimmen unveränderte Wahlzettel
* Kandidatenstimmen veränderte Wahlzettel
* Zusatzstimmen veränderte Wahlzettel
* Kandidaten-Nr
* Gewählt
* Name
* Vorname
* Stimmen unveränderte Wahlzettel
* Stimmen veränderte Wahlzettel
* Stimmen Total aus Wahlzettel
* Anzahl Gemeinden

Vorlage:
* XLS Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_sesam_proporz.xls]()
* CSV Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_sesam_proporz.csv]()
* XLSX Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_sesam_proporz.xlsx]()


#### Wabsti

##### Majorz-Wahl

Das Datenformat benötig zwei einzelne Tabellen: (1) Datenexport und (2) die Liste der gewählten Kandidaten.

###### (1) Datenexport

Im Datenexport gibt es für jede Gemeinde eine Zeile, Kandidaten sind in Spalten angeordnet. Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

* AnzMandate
* BFS
* StimmBer
* StimmAbgegeben
* StimmLeer
* StimmUngueltig
* StimmGueltig

Sowie für jeden Kandidaten
* KandID_``x``
* KandName_``x``
* KandVorname_``x``
* Stimmen_``x``

Zudem werden die leeren und ungültigen Stimmen auch als Kandidaten erfasst mittels der folgenden Kandidatennamen:
* KandName_``x`` = 'Leere Zeilen'
* KandName_``x`` = 'Ungültige Stimmen'

Vorlage:
* XLS Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_majorz_resultate.xls]()
* CSV Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_majorz_resultate.csv]()
* XLSX Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_majorz_resultate.xlsx]()

###### (2) Kandidatenresultate

Da das Datenformat keine Informationen über die gewählten Kandidaten liefert, müssen diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

* ID : Die ID des Kandidaten (``KandID_x``).
* Name : Der Familienname des Kandidaten.
* Vorname : Der Vorname des Kandidaten.

Vorlage:
* XLS Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_majorz_kandidaten.xls]()
* CSV Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_majorz_kandidaten.csv]()
* XLSX Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_majorz_kandidaten.xlsx]()


##### Proporz-Wahl

Das Datenformat benötig vier einzelne Tabellen: (1) Der Datenexport der Resultate, (2) der Datenexport der Statistiken, (3) die Listenverbindungen und (4) die Liste der gewählten Kandidaten.

###### (1) Datenexport der Resultate

Im Datenexport gibt es eine Zeile pro Kandidat und Gemeinde. Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

* Einheit_BFS
* Kand_Nachname
* Kand_Vorname
* Liste_KandID
* Liste_ID
* Liste_Code
* Kand_StimmenTotal
* Liste_ParteistimmenTotal

Vorlage:
* XLS Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_resultate.xls]()
* CSV Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_resultate.csv]()
* XLSX Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_resultate.xlsx]()

###### (2) Datenexport der Statistik

Die Datei mit den Statistiken zu den einzelnen Gemeinden sollte folgende Spalten enthalten:

* Einheit_BFS
* StimBerTotal
* WZEingegangen
* WZLeer
* WZUngueltig
* StmWZVeraendertLeerAmtlLeer

Vorlage:
* XLS Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_statistik.xls]()
* CSV Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_statistik.csv]()
* XLSX Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_statistik.xlsx]()

###### (3) Listenverbindungen

Die Datei mit den Listenverbindungen sollte folgende Spalten enthalten:

* Liste
* LV
* LUV

Vorlage:
* XLS Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_listenverbindungen.xls]()
* CSV Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_listenverbindungen.csv]()
* XLSX Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_listenverbindungen.xlsx]()


###### (4) Kandidatenresultate

Da das Datenformat keine Informationen über die gewählten Kandidaten liefert, müssen diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

* ID : Die ID des Kandidaten (``Liste_KandID``).
* Name : Der Familienname des Kandidaten.
* Vorname : Der Vorname des Kandidaten.

Vorlage:
* XLS Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_kandidaten.xls]()
* CSV Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_kandidaten.csv]()
* XLSX Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage_wahl_wabsti_proporz_kandidaten.xlsx]()


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
