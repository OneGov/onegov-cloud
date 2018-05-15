# Format Spezifikation Wahlen

Als Dateiformate werden CSV, XLS oder XLSX Dateien akzeptiert, welche von "Wabsti Wahlen und Abstimmungen (VRSG)" oder der Webapplikation selbst generiert werden. Falls eine Tabelle von Hand erstellt werden soll, ist das Format der Webapplikation (OneGov) am einfachsten.

## Inhalt

<!-- TOC START min:1 max:4 link:true update:true -->
- [Format Spezifikation Wahlen](#format-spezifikation-wahlen)
  - [Inhalt](#inhalt)
  - [Vorbemerkungen](#vorbemerkungen)
    - [Einheiten](#einheiten)
    - [Stille Wahlen](#stille-wahlen)
    - [Regionale Wahlen](#regionale-wahlen)
  - [Formate](#formate)
    - [OneGov](#onegov)
      - [Spalten](#spalten)
      - [Panaschierdaten](#panaschierdaten)
      - [Temporäre Resultate](#temporre-resultate)
      - [Vorlage](#vorlage)
    - [Wabsti Majorz](#wabsti-majorz)
      - [Spalten Datenexport](#spalten-datenexport)
      - [Spalten Kandidatenresultate](#spalten-kandidatenresultate)
      - [Temporäre Resultate](#temporre-resultate-1)
      - [Vorlagen](#vorlagen)
    - [Wabsti Proporz](#wabsti-proporz)
      - [Spalten Datenexport der Resultate](#spalten-datenexport-der-resultate)
      - [Panaschierdaten](#panaschierdaten-1)
      - [Spalten Datenexport der Statistik](#spalten-datenexport-der-statistik)
      - [Spalten Listenverbindungen](#spalten-listenverbindungen)
      - [Spalten Kandidatenresultate](#spalten-kandidatenresultate-1)
      - [Temporäre Resultate](#temporre-resultate-2)
      - [Vorlagen](#vorlagen-1)
    - [WabstiCExport Majorz](#wabsticexport-majorz)
    - [WabstiCExport Proporz](#wabsticexport-proporz)
    - [Parteiresultate](#parteiresultate)
      - [Vorlagen](#vorlagen-2)

<!-- TOC END -->

## Vorbemerkungen

### Einheiten

Eine Einheit entspricht einer Gemeinde (kantonale Instanzen, kommunale Instanzen ohne Stadtteilen) oder einem Stadtteil (kommunale Instanzen mit Stadtteilen).

### Stille Wahlen

Für stille Wahlen kann das OneGov Format verwendet werden. Alle Stimmen werden dabei auf `0` gesetzt.

### Regionale Wahlen

Bei regionalen Wahlen werden nur Wahlresultate der Einheiten eines Wahlkreises erwartet.

## Formate

### OneGov

Das Format, welche von der Web-Applikation für den Export verwendet wird, besteht aus einer einzelnen Datei pro Wahl. Es gibt für jede Einheit und Kandidat eine Zeile.

#### Spalten

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`election_absolute_majority`|Absolutes Mehr der Wahl, nur falls Majorzwahl.
`election_status`|`unknown`, `interim` oder `final`.
`entity_id`|BFS Nummer der Gemeinde oder ID des Stadtteils. Der Wert `0` kann für Auslandslebende verwendet werden.
`entity_counted`|`True`, wenn das Resultat ausgezählt wurde.
`entity_eligible_voters`|Anzahl Stimmberechtigte der Einheit.
`entity_received_ballots`|Anzahl abgegebene Stimmzettel der Einheit.
`entity_blank_ballots`|Anzahl leere Stimmzettel der Einheit.
`entity_invalid_ballots`|Anzahl ungültige Stimmzettel der Einheit.
`entity_blank_votes`|Anzahl leerer Stimmen der Einheit.
`entity_invalid_votes`|Anzahl ungültige Stimmen der Einheit. Null falls Proporzwahl.
`list_name`|Name der Liste des Kandidierenden. Nur bei Proporzwahlen.
`list_id`|ID der Liste des Kandidierenden. Nur bei Proporzwahlen.
`list_number_of_mandates`|Gesamte Anzahl der Mandate der Liste. Nur bei Proporzwahlen.
`list_votes`|Gesamte Anzahl der Listenstimmen. Nur bei Proporzwahlen.
`list_connection`|ID der Listenverbindung. Nur bei Proporzwahlen.
`list_connection_parent`|ID der übergeordneten Listenverbidnung. Nur bei Proporzwahlen und falls es sich um eine Unterlistenverbindung handelt.
`candidate_id`|ID des Kandidierenden.
`candidate_family_name`|Nachname des Kandidierenden.
`candidate_first_name`|Vorname des Kandidaten.
`candidate_elected`|True, falls der Kandidierenden gewählt wurde.
`candidate_party`|Der Name der Partei.
`candidate_votes`|Anzahl Kandidierendenstimmen in der Einheit.

#### Panaschierdaten

Die Resultate können Panaschierdaten enthalten, indem pro Liste eine Spalte hinzugefügt wird:

Name|Beschreibung
---|---
`panachage_votes_from_list_{XX}`|Die Anzahl Stimmen von der Liste mit `list_id = XX`. Die `list_id` mit dem Wert `999` steht für die Blankoliste.

#### Temporäre Resultate

Einheiten gelten als noch nicht ausgezählt, falls eine der beiden folgenden Bedingungen zutrifft:
- `counted = false`
- die Einheit ist nicht in den Resultaten enthalten

Falls der Status
- `interim` ist, gilt die Wahl als noch nicht abgeschlossen
- `final` ist, gilt die Wahl als abgeschlossen
- `unknown` ist, gilt die Wahl als abgeschlossen, falls alle (erwarteten) Einheiten ausgezählt sind

#### Vorlage

- [election_onegov_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_onegov_proporz.csv)

### Wabsti Majorz

Das Datenformat benötig zwei einzelne Tabellen: den Datenexport und die Liste der gewählten Kandidaten.

#### Spalten Datenexport

Im Datenexport gibt es für jede Einheit eine Zeile, Kandidaten sind in Spalten angeordnet. Es werden folgende Spalten ausgewertet und sollten vorhanden sein:
- `AnzMandate`
- `BFS`
- `StimmBer`
- `StimmAbgegeben`
- `StimmLeer`
- `StimmUngueltig`
- `StimmGueltig`

Sowie für jeden Kandidaten:
- `KandID_{XX}`
- `KandName_{XX}`
- `KandVorname_{XX}`
- `Stimmen_{XX}`

Zudem werden die leeren und ungültigen Stimmen auch als Kandidaten erfasst mittels der folgenden Kandidatennamen:
- `KandName_{XX} = 'Leere Zeilen'` (Leere Stimmen)
- `KandName_{XX} = 'Ungültige Stimmen'`

#### Spalten Kandidatenresultate

Da das Datenformat nicht zwingend Informationen über die gewählten Kandidaten liefert, können diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

Name|Beschreibung
---|---
`KandID`|Die ID des Kandidaten (`KandID_{XX}`).

#### Temporäre Resultate

Das Datenformat enthält keine eindeutige Informationen dazu, ob die gesamte Wahl fertig ausgezählt ist. Diese Information muss direkt auf dem Formular für den Datenupload mitgeben werden.

Das Datenformat enthält auch keine Information dazu, ob eine einzelne Einheit fertig ausgezählt ist. Falls Einheiten ganz fehlen in den Resultaten, gelten diese als noch nicht ausgezählt.

#### Vorlagen

- [election_wabsti_majorz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_majorz_candidates.csv)

### Wabsti Proporz

Das Datenformat benötig vier einzelne Tabellen: den Datenexport der Resultate, der Datenexport der Statistiken, die Listenverbindungen und die Liste der gewählten Kandidaten.

#### Spalten Datenexport der Resultate

Im Datenexport gibt es eine Zeile pro Kandidat und Einheit. Es werden folgende Spalten ausgewertet und sollten vorhanden sein:
- `Einheit_BFS`
- `Kand_Nachname`
- `Kand_Vorname`
- `Liste_KandID`
- `Liste_ID`
- `Liste_Code`
- `Kand_StimmenTotal`
- `Liste_ParteistimmenTotal`

#### Panaschierdaten

Die Resultate können Panaschierdaten enthalten, indem pro Liste eine Spalte hinzugefügt wird (`{List ID}.{List Code}`: die Anzahl Stimmen von der Liste mit `Liste_ID`). Die `Liste_ID` mit dem Wert `99` (`99.WoP`) steht für die Blankoliste.

#### Spalten Datenexport der Statistik

Die Datei mit den Statistiken zu den einzelnen Einheiten sollte folgende Spalten enthalten:
- `Einheit_BFS`
- `Einheit_Name`
- `StimBerTotal`
- `WZEingegangen`
- `WZLeer`
- `WZUngueltig`
- `StmWZVeraendertLeerAmtlLeer`

#### Spalten Listenverbindungen

Die Datei mit den Listenverbindungen sollte folgende Spalten enthalten:
- `Liste`
- `LV`
- `LUV`

#### Spalten Kandidatenresultate

Da das Datenformat keine Informationen über die gewählten Kandidaten liefert, müssen diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

Name|Beschreibung
---|---
`Liste_KandID`|Die ID des Kandidaten.

#### Temporäre Resultate

Das Datenformat enthält keine eindeutige Informationen dazu, ob die gesamte Wahl fertig ausgezählt ist. Diese Information muss direkt auf dem Formular für den Datenupload mitgeben werden.

Das Datenformat enthält auch keine Information dazu, ob eine einzelne Einheit fertig ausgezählt ist. Falls Einheiten ganz fehlen in den Resultaten, gelten diese als noch nicht ausgezählt.

#### Vorlagen

- [election_wabsti_proporz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_results.csv)
- [electionwabsti_proporz_statistics.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_statistics.csv)
- [electionwabsti_proporz_list_connections.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_list_connections.csv)
- [electionwabsti_proporz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_wabsti_proporz_candidates.csv)

### WabstiCExport Majorz

Es wird die Version `>= 2.2` unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumentation des Exporter-Programms definiert.

### WabstiCExport Proporz

Es wird die Version `>= 2.2` unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumentation des Exporter-Programms definiert.


### Parteiresultate

Jede Proporzwahl kann Parteiresultate enthalten. Diese sind unabhängig von den anderen Resultaten und beinhalten typischerweise die aggregierten Resultate der verschiedenen Listen einer einzelnen Partei.

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`year`|Das Jahr der Wahl.
`total_votes`|Die Gesamtanzahl der Stimmen der Wahl.
`name`|Der Name der Partei.
`id`|ID der Partei (beliebige Zahl).
`color`|Die Farbe der Partei.
`mandates`|Die Anzahl Mandate der Partei.
`votes`|Die Anzahl Stimmen der Partei.

Die Resultate können Panaschierdaten enthalten, indem pro Partei eine Spalte hinzugefügt wird:

Name|Beschreibung
---|---
`panachage_votes_from_{XX}`|Die Anzahl Stimmen von der Partei mit `id = XX`. Die `id` mit dem Wert `999` steht für die Stimmen aus der Blankoliste.

Panaschierdaten werden nur hinzugefügt, falls:
- `year` entspricht dem Jahr der Wahl
- `id (XX)` entspricht nicht `id` der Zeile

#### Vorlagen

- [election_party_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/election_party_results.csv)
