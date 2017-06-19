Format Spezifikation Wahlen
============================

Als Dateiformate werden CSV, XLS oder XLSX Dateien akzeptiert, welche von "Wabsti Wahlen und Abstimmungen (VRSG)" oder der Webapplikation selbst generiert werden. Falls eine Tabelle von Hand erstellt werden soll, ist das Format der Webapplikation am einfachsten.

Eine "Gemeinde" kann auch ein Bezirk, ein Wahlkreis etc. sein.

## Inhalt

1. [OneGov](#1-onegov)
2. [Wabsti Majorz](#2-wabsti-majorz)
3. [Wabsti Proporz](#3-wabsti-proporz)
4. [WabstiCExport Majorz](#4-wabsticexport-majorz)
5. [WabstiCExport Proporz](#5-wabsticexport-proporz)
6. [Parteiresultate](#6-parteiresultate)

1 OneGov
----------

Das Format, welche von der Web-Applikation für den Export verwendet wird, besteht aus einer einzelnen Datei pro Wahl. Es gibt für jede Gemeinde und Kandidat eine Zeile.

### Spalten

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`election_absolute_majority`|Absolutes Mehr der Wahl, nur falls Majorzwahl.
`election_status`|`unknown`, `interim` oder `final`.
`election_counted_entities`|Anzahl ausgezählter Gemeinden. Falls `election_counted_entities = election_total_entities` ist, gilt die Wahl als fertig ausgezählt.
`election_total_entities`|Totale Anzahl Gemeinden. Falls keine eindeutige Auskunft über den Status der Wahl möglich ist (da die Wahl von Wabsti importiert wurde), ist dieser Wert `0`.
`entity_id`|BFS Nummer der Gemeinde. Der Wert `0` kann für Auslandslebende verwendet werden.
`entity_name`|Der Name der Gemeinde.
`entity_elegible_voters`|Anzahl Stimmberechtigte der Gemeinde.
`entity_received_ballots`|Anzahl abgegebene Stimmzettel der Gemeinde.
`entity_blank_ballots`|Anzahl leere Stimmzettel der Gemeinde.
`entity_invalid_ballots`|Anzahl ungültige Stimmzettel der Gemeinde.
`entity_blank_votes`|Anzahl leerer Stimmen der Gemeinde.
`entity_invalid_votes`|Anzahl ungültige Stimmen der Gemeinde. Null falls Proporzwahl.
`list_name`|Name der Liste des Kandidierenden. Nur bei Proporzwahlen.
`list_id`|ID der Liste des Kandidierenden. Nur bei Proporzwahlen.
`list_number_of_mandates`|Gesamte Anzahl der Mandate der Liste. Nur bei Proporzwahlen.
`list_votes`|Gesamte Anzahl der Listenstimmen. Nur bei Proporzwahlen.
`list_connection`|ID der Listenverbindung. Nur bei Proporzwahlen.
`list_connection_parent`|ID der übergeordneten Listenverbidnung. Nur bei Proporzwahlen und falls es sich um eine Unterlistenverbindung handelt.
`candidate_family_name`|Nachnahme des Kandidierenden.
`candidate_first_name`|Vorname des Kandidaten.
`candidate_elected`|True, falls der Kandidierenden gewählt wurde.
`candidate_party`|Der Name der Partei.
`candidate_votes`|Anzahl Kandidierendenstimmen in der Gemeinde.

#### Panaschierdaten

Die Resultaten können Panaschierdaten enthalten, indem pro Liste eine Spalte hinzugefügt wird:

Name|Beschreibung
---|---
`panachage_votes_from_list_{XX}`|Die Anzahl Stimmen von der Liste mit `list_id = XX`. Die `list_id` mit dem Wert `999` steht für die Blankoliste.

### Temporäre Resultate

Noch nicht ausgezählte Gemeinden sind nicht in den Daten enthalten.

Falls der Status
- `interim` ist, gilt die Abstimmung als noch nicht abgeschlossen
- `final` ist, gilt die Abstimmung als abgeschlossen
- `unknown` ist, gilt die Abstimmung als abgeschlossen, falls alle `election_counted_entities` und `election_total_entities` übereinstimmen


### Vorlage

- [election_onegov_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_proporz.csv)

2 Wabsti Majorz
---------------

Das Datenformat benötig zwei einzelne Tabellen: den Datenexport und die Liste der gewählten Kandidaten.

### Spalten Datenexport

Im Datenexport gibt es für jede Gemeinde eine Zeile, Kandidaten sind in Spalten angeordnet. Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`AnzMandate`|
`BFS`|Die BFS Nummer der Gemeinde. Der Wert `0` kann für Auslandslebende verwendet werden.
`EinheitBez`|
`StimmBer`|
`StimmAbgegeben`|
`StimmLeer`|
`StimmUngueltig`|
`StimmGueltig`|

Sowie für jeden Kandidaten:

Name|Beschreibung
---|---
`KandID_{XX}`|
`KandName_{XX}`|
`KandVorname_{XX}`|
`Stimmen_{XX}`|

Zudem werden die leeren und ungültigen Stimmen auch als Kandidaten erfasst mittels der folgenden Kandidatennamen:

- `KandName_{XX} = 'Leere Zeilen'`
- `KandName_{XX} = 'Ungültige Stimmen'`

### Spalten Kandidatenresultate

Da das Datenformat keine Informationen über die gewählten Kandidaten liefert, müssen diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

Name|Beschreibung
---|---
`ID`|Die ID des Kandidaten (`KandID_{XX}`).
`Name`|Der Familienname des Kandidaten.
`Vorname`|Der Vorname des Kandidaten.

### Temporäre Resultate

Das Datenformat enthält keine eindeutige Informationen dazu, ob die gesamte Wahl fertig ausgezählt ist. Diese Information muss direkt auf dem Formular für den Datenupload mitgeben werden.

Das Datenformat enhält auch keine Information dazu, ob eine einzelne Gemeinde fertig ausgezählt ist. Daher wird, solange die gesamte Wahl nicht abgeschlossen ist, für Wabsti auch keine Fortschrittsanzeige angezeigt. Falls aber Gemeinden ganz fehlen in den Resultaten, gelten diese als noch nicht ausgezählt.

### Vorlagen

- [election_wabsti_majorz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_candidates.csv)

3 Wabsti Proporz
----------------

Das Datenformat benötig vier einzelne Tabellen: den Datenexport der Resultate, der Datenexport der Statistiken, die Listenverbindungen und die Liste der gewählten Kandidaten.

### Spalten Datenexport der Resultate

Im Datenexport gibt es eine Zeile pro Kandidat und Gemeinde. Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`Einheit_BFS`|Die BFS Nummer der Gemeinde. Der Wert `0` kann für Auslandslebende verwendet werden.
`Einheit_Name`|
`Kand_Nachname`|
`Kand_Vorname`|
`Liste_KandID`|
`Liste_ID`|
`Liste_Code`|
`Kand_StimmenTotal`|
`Liste_ParteistimmenTotal`|

#### Panaschierdaten

Die Resultaten können Panaschierdaten enthlaten, indem pro Liste eine Spalte hinzugefügt wird:

Name|Beschreibung
---|---
`{List ID}.{List Code}`|Die Anzahl Stimmen von der Liste mit `Liste_ID`. Die `Liste_ID` mit dem Wert `99` (`99.WoP`) steht für die Blankoliste.

### Spalten Datenexport der Statistik

Die Datei mit den Statistiken zu den einzelnen Gemeinden sollte folgende Spalten enthalten:

Name|Beschreibung
---|---
`Einheit_BFS`|
`Einheit_Name`|
`StimBerTotal`|
`WZEingegangen`|
`WZLeer`|
`WZUngueltig`|
`StmWZVeraendertLeerAmtlLeer`|

### Spalten Listenverbindungen

Die Datei mit den Listenverbindungen sollte folgende Spalten enthalten:

Name|Beschreibung
---|---
`Liste`|
`LV`|
`LUV`|

### Spalten Kandidatenresultate

Da das Datenformat keine Informationen über die gewählten Kandidaten liefert, müssen diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

Name|Beschreibung
---|---
`ID`|Die ID des Kandidaten (`Liste_KandID`).
`Name`|Der Familienname des Kandidaten.
`Vorname`|Der Vorname des Kandidaten.

### Temporäre Resultate

Das Datenformat enthält keine eindeutige Informationen dazu, ob die gesamte Wahl fertig ausgezählt ist. Diese Information muss direkt auf dem Formular für den Datenupload mitgeben werden.

Das Datenformat enhält auch keine Information dazu, ob eine einzelne Gemeinde fertig ausgezählt ist. Daher wird, solange die gesamte Wahl nicht abgeschlossen ist, für Wabsti auch keine Fortschrittsanzeige angezeigt. Falls aber Gemeinden ganz fehlen in den Resultaten, gelten diese als noch nicht ausgezählt.

### Vorlagen

- [election_wabsti_proporz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_results)
- [electionwabsti_proporz_statistics.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_statistics)
- [electionwabsti_proporz_list_connections.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_list_connections)
- [electionwabsti_proporz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_candidates.csv)

4 WabstiCExport Majorz
----------------------

Es wird die Version `2.2` wird unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumenation des Exporter-Programms definiert.

5 WabstiCExport Proporz
-----------------------

Es wird die Version `2.2` wird unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumenation des Exporter-Programms definiert.


6 Parteiresultate
-----------------

Jede Proporzwahl kann Parteiresultate enthalten. Diese sind unabhängig von den anderen Resultaten und beinhalten typischerweise die aggregierten Resultate der verschiedenen Listen einer einzelnen Partei.

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`year`|Das Jahr der Wahl.
`total_votes`|Die Gesamtanzahl der Stimmen der Wahl.
`name`|Der Name der Partei.
`color`|Die Farbe der Partei.
`mandates`|Die Anzahl Mandate der Partei.
`votes`|Die Anzahl Stimmen der Partei.


### Template

- [election_party_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_party_results.csv)
