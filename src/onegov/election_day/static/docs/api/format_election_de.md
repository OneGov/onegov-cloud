# Format Spezifikation Wahlen

Als Dateiformate werden CSV, XLS oder XLSX Dateien akzeptiert, welche von "Wabsti Wahlen und Abstimmungen (VRSG)" oder der Webapplikation selbst generiert werden. Falls eine Tabelle von Hand erstellt werden soll, ist das Format der Webapplikation (OneGov) am einfachsten.

## Inhalt

<!-- https://atom.io/packages/atom-mdtoc -->
<!-- MDTOC maxdepth:6 firsth1:2 numbering:1 flatten:0 bullets:1 updateOnSave:1 -->

- 1. [Inhalt](#Inhalt)
- 2. [Vorbemerkungen](#Vorbemerkungen)
   - 2.1. [Einheiten](#Einheiten)
   - 2.2. [Stille Wahlen](#Stille-Wahlen)
   - 2.3. [Regionale Wahlen](#Regionale-Wahlen)
- 3. [Formate](#Formate)
   - 3.1. [OneGov](#OneGov)
      - 3.1.1. [Spalten](#Spalten)
      - 3.1.2. [Panaschierdaten](#Panaschierdaten)
      - 3.1.3. [Temporäre Resultate](#Temporare-Resultate)
      - 3.1.4. [Verbundene Wahlen](#Verbundene-Wahlen)
      - 3.1.5. [Vorlage](#Vorlage)
   - 3.2. [Wabsti Majorz](#Wabsti-Majorz)
      - 3.2.1. [Spalten Datenexport](#Spalten-Datenexport)
      - 3.2.2. [Spalten Kandidatenresultate](#Spalten-Kandidatenresultate)
      - 3.2.3. [Temporäre Resultate](#Temporare-Resultate-1)
      - 3.2.4. [Vorlagen](#Vorlagen)
   - 3.3. [Wabsti Proporz](#Wabsti-Proporz)
      - 3.3.1. [Spalten Datenexport der Resultate](#Spalten-Datenexport-der-Resultate)
      - 3.3.2. [Panaschierdaten](#Panaschierdaten-1)
      - 3.3.3. [Spalten Datenexport der Statistik](#Spalten-Datenexport-der-Statistik)
      - 3.3.4. [Spalten Listenverbindungen](#Spalten-Listenverbindungen)
      - 3.3.5. [Spalten Kandidatenresultate](#Spalten-Kandidatenresultate-1)
      - 3.3.6. [Temporäre Resultate](#Temporare-Resultate-2)
      - 3.3.7. [Vorlagen](#Vorlagen-1)
   - 3.4. [WabstiCExport Majorz](#WabstiCExport-Majorz)
   - 3.5. [WabstiCExport Proporz](#WabstiCExport-Proporz)
   - 3.6. [Parteiresultate](#Parteiresultate)
      - 3.6.1. [Einflussbereich](#Einflussbereich)
      - 3.6.2. [Panaschierdaten](#Panaschierdaten-2)
      - 3.6.3. [Vorlagen](#Vorlagen-2)
   - 3.7. [Automatische Erstellung verbundene Wahl und Wahlen mit REST-API](#Automatische-Erstellung-verbundene-Wahl-und-Wahlen-mit-REST-API)

<!-- /MDTOC -->


## Vorbemerkungen

### Einheiten

Eine Einheit entspricht einer Gemeinde (kantonale Instanzen, kommunale Instanzen ohne Stadtteilen) oder einem Stadtteil (kommunale Instanzen mit Stadtteilen).

### Stille Wahlen

Für stille Wahlen kann das OneGov Format verwendet werden. Alle Stimmen werden dabei auf `0` gesetzt.

### Regionale Wahlen

Bei regionalen Wahlen werden nur Wahlresultate der Einheiten eines Wahlkreises erwartet, falls die entsprechende Option gesetzt ist auf der Wahl.

## Formate

### OneGov

Das Format, welche von der Web-Applikation für den Export verwendet wird, besteht aus einer einzelnen Datei pro Wahl. Es gibt für jede Einheit und Kandidat eine Zeile.

#### Spalten

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`election_absolute_majority`|Absolutes Mehr der Wahl, nur falls Majorzwahl.
`election_status`|Status der Wahl. `interim` (Zwischenresultate), `final` (Endresultate) oder `unknown` (unbekannt).
`entity_id`|BFS Nummer der Gemeinde oder ID des Stadtteils. Der Wert `0` kann für Auslandslebende verwendet werden.
`entity_counted`|`True`, wenn das Resultat ausgezählt wurde.
`entity_eligible_voters`|Anzahl Stimmberechtigte der Einheit.
`entity_expats`|Anzahl Auslandslebende der Einheit. Optional.
`entity_received_ballots`|Anzahl abgegebene Stimmzettel der Einheit.
`entity_blank_ballots`|Anzahl leere Stimmzettel der Einheit.
`entity_invalid_ballots`|Anzahl ungültige Stimmzettel der Einheit.
`entity_blank_votes`|Anzahl leerer Stimmen der Einheit.
`entity_invalid_votes`|Anzahl ungültige Stimmen der Einheit. Null falls Proporzwahl.
`list_name`|Name der Liste des Kandidierenden. Nur bei Proporzwahlen.
`list_id`|ID der Liste des Kandidierenden. Nur bei Proporzwahlen. Kann alphanumerisch oder numerisch sein.
`list_color`|Die Farbe der Liste als Hexadezimalwert, z.B. `#a6b784'. Nur bei Proporzwahlen.
`list_number_of_mandates`|Gesamte Anzahl der Mandate der Liste. Nur bei Proporzwahlen.
`list_votes`|Anzahl der Listenstimmen pro Gemeinde. Nur bei Proporzwahlen.
`list_connection`|ID der Listenverbindung oder Unterlistenverbindung (wenn list_connetion_parent vorhanden). Nur bei Proporzwahlen.
`list_connection_parent`|ID der übergeordneten Listenverbidnung. Nur bei Proporzwahlen. Muss leer sein, wenn keine Unterlistenverbindung vorhanden.
`candidate_id`|ID des Kandidierenden.
`candidate_family_name`|Nachname des Kandidierenden.
`candidate_first_name`|Vorname des Kandidaten.
`candidate_elected`|True, falls der Kandidierenden gewählt wurde.
`candidate_party`|Der Name der Partei.
`candidate_party_color`|Die Farbe der Partei als Hexadezimalwert, z.B. `#a6b784'.
`candidate_gender`|Das Geschlecht des Kandidierenden: `female` (weiblich), `male` (männlich) oder `undetermined` (unbestimmt). Optional.
`candidate_year_of_birth`|Der Jahrgang des Kandidierenden. Optional.
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

Für den Status
- `interim` gilt die Wahl als noch nicht abgeschlossen
- `final` gilt die Wahl als abgeschlossen
- `unknown` gilt die Wahl als abgeschlossen, falls alle (erwarteten) Einheiten ausgezählt sind

#### Verbundene Wahlen

Die Resultate von verbundenen Wahlen können gebündelt hochgeladen werden, indem eine einzige Datei mit allen Zeilen der Resultate der einzelnen Wahlen geliefert wird.

#### Vorlage

- [election_onegov_majorz.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_onegov_majorz.csv)
- [election_onegov_proporz.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_onegov_proporz.csv)

### Wabsti Majorz

Das Datenformat benötigt zwei einzelne Tabellen: den Datenexport und die Liste der gewählten Kandidaten.

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

Da das Datenformat nicht zwingend Informationen über die gewählten Kandidaten liefert, können diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei einen gewählten Kandidaten mit den folgenden Spalten:

Name|Beschreibung
---|---
`KandID`|Die ID des Kandidaten (`KandID_{XX}`).

#### Temporäre Resultate

Das Datenformat enthält keine eindeutige Informationen dazu, ob die gesamte Wahl fertig ausgezählt ist. Diese Information muss direkt auf dem Formular für den Datenupload mitgeben werden.

Das Datenformat enthält auch keine Information dazu, ob eine einzelne Einheit fertig ausgezählt ist. Falls Einheiten ganz fehlen in den Resultaten, gelten diese als noch nicht ausgezählt.

#### Vorlagen

- [election_wabsti_majorz_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_majorz_results.csv)
- [election_wabsti_majorz_candidates.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_majorz_candidates.csv)

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

- [election_wabsti_proporz_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_results.csv)
- [electionwabsti_proporz_statistics.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_statistics.csv)
- [electionwabsti_proporz_list_connections.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_list_connections.csv)
- [electionwabsti_proporz_candidates.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_wabsti_proporz_candidates.csv)

### WabstiCExport Majorz

Es wird die Version `>= 2.2` unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumentation des Exporter-Programms definiert.

### WabstiCExport Proporz

Es wird die Version `>= 2.2` unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumentation des Exporter-Programms definiert.


### Parteiresultate

Jede Proporzwahl und jede verbundene Wahl kann Parteiresultate enthalten. Diese sind unabhängig von den anderen Resultaten und beinhalten typischerweise die aggregierten Resultate der verschiedenen Listen einer einzelnen Partei.

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`domain`|Der Einflussbereich, für den die Zeile gilt. Optional.
`domain_segment`|Die Einheit des Einflussbereichs, für die die Zeile gilt. Optional.
`year`|Das Jahr der Wahl.
`total_votes`|Die Gesamtanzahl der Stimmen der Wahl.
`name`|Der Name der Partei in der Standardsprache. Optional*.
`name_{locale}`|Übersetzter Name der Partei, z. B. `name_de_ch` für den deutschen Namen. Optional. Stellen Sie sicher, dass Sie den Namen der Partei in der Standardsprache entweder in der Spalte `name` oder `name_{default_locale}` angeben.
`id`|ID der Partei (beliebige Zahl).
`color`|Die Farbe der Partei als Hexadezimalwert, z.B. `#a6b784'.
`mandates`|Die Anzahl Mandate der Partei.
`votes`|Die Anzahl Stimmen der Partei.
`voters_count`|Wählerzahlen. Die kumulierte Anzahl Stimmen pro Gesamtanzahl Mandate pro Wahl. Nur für verbundene Wahlen.
`voters_count_percentage`|Wählerzahlen (prozentual). Die kumulierte Anzahl Stimmen pro Gesamtanzahl Mandate pro Wahl (prozentual). Nur für verbundene Wahlen.

#### Einflussbereich

`domain` und `domain_segment` ermöglichen, Parteiresultate für einen anderen Einflussbereich als den der Wahl oder des Verbundes zu erfassen. `domain` entspricht dabei einem untergeordneten Einflussbereichs der Wahl oder des Verbundes, z.B. bei kantonalen Parlamentswahlen je nach Kanton `superregion`, `region`, `district` oder `municipality`. `domain_segment` entspricht einer Einheit in diesem untergeordneten Einflussbereich, z.B. `Region 1`, `Bergün`, `Toggenburg` oder `Zug`. Im Normalfall können sowohl `domain` als auch `domain_segment` leer oder weggelassen werden, `domain` wird in diesem Fall implizit auf den `domain` der Wahl oder des Verbundes gesetzt. Aktuell wird nur der `domain` der Wahl oder des Verbundes sowie `domain = 'superregion'` bei verbundenen Wahlen unterstützt.

#### Panaschierdaten

Die Resultate können Panaschierdaten enthalten, indem pro Partei eine Spalte hinzugefügt wird:

Name|Beschreibung
---|---
`panachage_votes_from_{XX}`|Die Anzahl Stimmen von der Partei mit `id = XX`. Die `id` mit dem Wert `999` steht für die Stimmen aus der Blankoliste.

Panaschierdaten werden nur hinzugefügt, falls:
- `year` entspricht dem Jahr der Wahl
- `id (XX)` entspricht nicht `id` der Zeile

#### Vorlagen

- [election_party_results.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/election_party_results.csv)

### Automatische Erstellung verbundene Wahl und Wahlen mit REST-API

Mit der WabstiC Export Version 2.4.3 können verbundene Wahlen mithilfe der Datei `WP_Wahl.csv` erstellt werden.
Das Token wird unter **WabstiDatenquellen** erzeugt.

    curl https://[base_url]/create-wabsti-proporz \
      --user :[token] \
      --header "Accept-Language: de_CH" \
      --form "wp_wahl=@WP_Wahl.csv"

Dieser Endpunkt erstellt dann folgendes:

1. Alle Wahlen, die in `WP_Wahl.csv` vorhanden sind.
2. Die verbundene Wahl
3. Je eine Zuordnung für jede Wahl zur Wabsti Datenquelle, um Resultate hochzuladen.
