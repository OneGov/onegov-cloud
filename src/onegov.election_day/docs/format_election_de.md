# Format Spezifikation Wahlen

Als Dateiformate werden CSV, XLS oder XLSX Dateien akzeptiert, welche von den Wahlprogrammen "Wahlen (SESAM)" und "Wabsti Wahlen und Abstimmungen (VRSG)", oder der Webapplikation selbst generiert werden. Falls eine Tabelle von Hand erstellt werden soll, ist das Format der Webapplikation am einfachsten.

## Inhalt

[SESAM Majorz](#sesam-majorz)

[SESAM Proporz](#sesam-proporz)

[Wabsti Majorz](#wabsti-majorz)

[Wabsti Proporz](#wabsti-proporz)

[OneGov](#onegov)


## SESAM Majorz

Das SESAM-Export-Format enthält direkt alle benötigten Daten. Es gibt pro Kandidat und Gemeinde eine Zeile.

### Spalten

Folgende Spalten werden ausgewertet und sollten mindestens vorhanden sein:

- **Anzahl Sitze**
- **Wahlkreis-Nr**
- **Anzahl Gemeinden**
- **Stimmberechtigte**
- **Wahlzettel**
- **Ungültige Wahlzettel**
- **Leere Wahlzettel**
- **Leere Stimmen**
- **Ungueltige Stimmen**
- **Kandidaten-Nr**
- **Gewaehlt**
- **Name**
- **Vorname**
- **Stimmen**

### Temporäre Resultate

Die Wahl gilt als noch nicht ausgezählt, falls in ``Anzahl Gemeinden`` die Anzahl ausgezählte Gemeinden nicht mit der Gesamtanzahl an Gemeinden übereinstimmt. Noch nicht ausgezählte Gemeinden sind nicht in den Daten enthalten.

### Vorlage

[election_sesam_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_sesam_majorz.csv)

## SESAM Proporz

Das SESAM-Export-Format enthält direkt alle benötigten Daten. Es gibt pro Kandidat und Gemeinde eine Zeile.

### Spalten

Folgende Spalten werden ausgewertet und sollten mindestens vorhanden sein:

- **Anzahl Sitze**
- **Wahlkreis-Nr**
- **Stimmberechtigte**
- **Wahlzettel**
- **Ungültige Wahlzettel**
- **Leere Wahlzettel**
- **Leere Stimmen**
- **Listen-Nr**
- **Partei-ID**
- **Parteibezeichnung**
- **HLV-Nr**
- **ULV-Nr**
- **Anzahl Sitze Liste**
- **Kandidatenstimmen unveränderte Wahlzettel** (Teil der Listenstimmen)
- **Zusatzstimmen unveränderte Wahlzettel** (Teil der Listenstimmen)
- **Kandidatenstimmen veränderte Wahlzettel** (Teil der Listenstimmen)
- **Zusatzstimmen veränderte Wahlzettel** (Teil der Listenstimmen)
- **Kandidaten-Nr**
- **Gewählt**
- **Name**
- **Vorname**
- **Stimmen Total aus Wahlzettel**
- **Anzahl Gemeinden**

### Temporäre Resultate

Die Wahl gilt als noch nicht ausgezählt, falls in ``Anzahl Gemeinden`` die Anzahl ausgezählte Gemeinden nicht mit der Gesamtanzahl an Gemeinden übereinstimmt. Noch nicht ausgezählte Gemeinden sind nicht in den Daten enthalten.

### Vorlage

[election_sesam_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_sesam_proporz.csv)

## Wabsti Majorz

Das Datenformat benötig zwei einzelne Tabellen: den Datenexport und die Liste der gewählten Kandidaten.

### Spalten Datenexport

Im Datenexport gibt es für jede Gemeinde eine Zeile, Kandidaten sind in Spalten angeordnet. Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

- **AnzMandate**
- **BFS**
- **StimmBer**
- **StimmAbgegeben**
- **StimmLeer**
- **StimmUngueltig**
- **StimmGueltig**

Sowie für jeden Kandidaten:

- **KandID_``x``**
- **KandName_``x``**
- **KandVorname_``x``**
- **Stimmen_``x``**

Zudem werden die leeren und ungültigen Stimmen auch als Kandidaten erfasst mittels der folgenden Kandidatennamen:

- **KandName_``x`` = 'Leere Zeilen'**
- **KandName_``x`` = 'Ungültige Stimmen'**

### Spalten Kandidatenresultate

Da das Datenformat keine Informationen über die gewählten Kandidaten liefert, müssen diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

- **ID** : Die ID des Kandidaten (``KandID_x``).
- **Name** : Der Familienname des Kandidaten.
- **Vorname** : Der Vorname des Kandidaten.

### Temporäre Resultate

Das Datenformat enthält keine eindeutige Informationen dazu, ob die gesamte Wahl fertig ausgezählt ist. Diese Information muss direkt auf dem Formular für den Datenupload mitgeben werden.

Das Datenformat enhält auch keine Information dazu, ob eine einzelne Gemeinde fertig ausgezählt ist. Daher wird, solange die gesamte Wahl nicht abgeschlossen ist, für Wabsti auch keine Fortschrittsanzeige angezeigt. Falls aber Gemeinden ganz fehlen in den Resultaten, gelten diese als noch nicht ausgezählt.

### Vorlagen

[election_wabsti_majorz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_majorz_results.csv)

[election_wabsti_majorz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_majorz_candidates.csv)

## Wabsti Proporz

Das Datenformat benötig vier einzelne Tabellen: den Datenexport der Resultate, der Datenexport der Statistiken, die Listenverbindungen und die Liste der gewählten Kandidaten.

### Spalten Datenexport der Resultate

Im Datenexport gibt es eine Zeile pro Kandidat und Gemeinde. Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

- **Einheit_BFS**
- **Kand_Nachname**
- **Kand_Vorname**
- **Liste_KandID**
- **Liste_ID**
- **Liste_Code**
- **Kand_StimmenTotal**
- **Liste_ParteistimmenTotal**

### Spalten  Datenexport der Statistik

Die Datei mit den Statistiken zu den einzelnen Gemeinden sollte folgende Spalten enthalten:

- **Einheit_BFS**
- **StimBerTotal**
- **WZEingegangen**
- **WZLeer**
- **WZUngueltig**
- **StmWZVeraendertLeerAmtlLeer**

### Spalten Listenverbindungen

Die Datei mit den Listenverbindungen sollte folgende Spalten enthalten:

- **Liste**
- **LV**
- **LUV**

### Spalten Kandidatenresultate

Da das Datenformat keine Informationen über die gewählten Kandidaten liefert, müssen diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

- **ID**: Die ID des Kandidaten (``Liste_KandID``).
- **Name**: Der Familienname des Kandidaten.
- **Vorname**: Der Vorname des Kandidaten.

### Temporäre Resultate

Das Datenformat enthält keine eindeutige Informationen dazu, ob die gesamte Wahl fertig ausgezählt ist. Diese Information muss direkt auf dem Formular für den Datenupload mitgeben werden.

Das Datenformat enhält auch keine Information dazu, ob eine einzelne Gemeinde fertig ausgezählt ist. Daher wird, solange die gesamte Wahl nicht abgeschlossen ist, für Wabsti auch keine Fortschrittsanzeige angezeigt. Falls aber Gemeinden ganz fehlen in den Resultaten, gelten diese als noch nicht ausgezählt.

### Vorlagen

[election_wabsti_proporz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_results.csv)

[election_wabsti_proporz_statistics.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_statistics.csv)

[election_wabsti_proporz_list_connections.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_list_connections.csv)

[election_wabsti_proporz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_candidates.csv)


## OneGov

Das Format, welche von der Web-Applikation für den Export verwendet wird, besteht aus einer einzelnen Datei pro Wahl. Es gibt für jede Gemeinde und Kandidat eine Zeile.

### Spalten

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

- **election_absolute_majority**: Absolutes Mehr der Wahl, nur falls Majorzwahl.
- **election_counted_municipalites**: Anzahl ausgezählter Gemeinden. Falls ``election_counted_municipalites = election_total_municipalites`` ist, gilt die Wahl als fertig ausgezählt.
- **election_total_municipalites**: Totale Anzahl Gemeinden. Falls keine eindeutige Auskunft über den Status der Wahl möglich ist (da die Wahl von Wabsti importiert wurde), ist dieser Wert ``0``.
- **municipality_bfs_number**: BFS Nummer der Gemeinde.
- **municipality_elegible_voters**: Anzahl Stimmberechtigte der Gemeinde.
- **municipality_received_ballots**: Anzahl abgegebene Stimmzettel der Gemeinde.
- **municipality_blank_ballots**: Anzahl leere Stimmzettel der Gemeinde.
- **municipality_invalid_ballots**: Anzahl ungültige Stimmzettel der Gemeinde.
- **municipality_blank_votes**: Anzahl leerer Stimmen der Gemeinde.
- **municipality_invalid_votes**: Anzahl ungültige Stimmen der Gemeinde. Null falls Proporzwahl.
- **list_name**: Name der Liste des Kandidierenden. Nur bei Proporzwahlen.
- **list_id**: ID der Liste des Kandidierenden. Nur bei Proporzwahlen.
- **list_number_of_mandates**: Gesamte Anzahl der Mandate der Liste. Nur bei Proporzwahlen.
- **list_votes**: Gesamte Anzahl der Listenstimmen. Nur bei Proporzwahlen.
- **list_connection**: ID der Listenverbindung. Nur bei Proporzwahlen.
- **list_connection_parent**: ID der übergeordneten Listenverbidnung. Nur bei Proporzwahlen und falls es sich um eine Unterlistenverbindung handelt.
- **candidate_family_name**: Nachnahme des Kandidierenden.
- **candidate_first_name**: Vorname des Kandidaten.
- **candidate_elected**: True, falls der Kandidierenden gewählt wurde.
- **candidate_votes**: Anzahl Kandidierendenstimmen in der Gemeinde.

### Temporäre Resultate

Die Wahl gilt als noch nicht ausgezählt, falls ``election_counted_municipalites`` und ``election_total_municipalites`` nicht übereinstimmen. Falls ``election_total_municipalites = 0`` ist, ist keine eindeutige Auskunft über den Status der Wahl möglich ist (da die Wahl von Wabsti importiert wurde).

Noch nicht ausgezählte Gemeinden sind nicht in den Daten enthalten.


### Vorlage

[election_onegov_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_onegov_majorz.csv)

[election_onegov_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_onegov_proporz.csv)
