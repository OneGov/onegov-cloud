Wahlen & Abstimmungen: Open Data
================================

## Einleitung

Für jede wichtige Seite gibt es eine enstprechende JSON-Alternative. Alle Responses enthalten den `Last-Modified` HTTP Header, welcher Auskunft über den Zeitpunkt der letzten Änderung gibt (z.B., wann zum letzten Mal Ergebnisse einer Wahl oder Abstimmung hochgeladen wurden).

Eine "Gemeinde" kann auch ein Bezirk, ein Wahlkreis etc. sein.

Inhalt
------

1. [Ergebnisübersicht](#1-ergebnisübersicht)
2. [Wahlresultate](#2-wahlresultate)
3. [Abstimmungsresultate](#3-abstimmungsresultate)

1 Ergebnisübersicht
-------------------

```
URL (letzte): /json
URL (Archiv nach Jahr): /archive/{Jahr}/json
URL (Archiv nach Datum): /archive/{Jahr}-{Monat}-{Tag}/json
URL (Wahl): /election/{id}/summary
URL (Abstimmung): /vote/{id}/summary
```

Die auf der Startseite und den Archivseiten dargestellten Ergebnisse sind im JSON Format verfügbar. Die Daten enthalten neben einigen globalen Informationen für jede Wahl / Abstimmung die folgenden Informationen:

Name|Beschreibung
---|---
`type`|`election` für Wahlen, `vote` für Abstimmungen.
`title`|Ein Objekt mit den übersetzten Titeln.
`date`|Das Datum (ISO 8601).
`domain`|Einflussbereich (Bund, Kanton, ...).
`url`|Ein Link zur Detailansicht.
`completed`|True, falls die Abstimmung oder Wahl abgeschlossen ist.
`progess`|Ein Objekt welches die Anzahl ausgezählter Gemeinden (`counted`) und die Gesamtzahl an Gemeinden (`total`) enthält.


Abstimmungsresultate enthalten die folgenden zusätzlichen Informationen:

Name|Beschreibung
---|---
`answer`|Das Abstimmungsresultat: `accepted` (angenommen), `rejected` (abgelehnt), `proposal` (Initiative) oder `counter-proposal` (Gegenvorschlag).
`yeas_percentage`|Ja-Stimmen in Prozent.
`nays_percentage`|Nein-Stimmen in Prozent.
`local` (*optional*)|Eidgenössische und kantonale Abstimmungen innerhalb kommunaler Instanzen können zusätzlich die Resultate dieser Gemeinde enthalten als zusätzliches Objekt mit den Feldern `answer`, `yeas_percentage` and `nays_percentage`.

2 Wahlresultate
---------------

### Aufbereitete Ergebnisse

```
URL: /election/{id}/json
```

Es werden dieselben Daten wie in der normalen Ansicht in einer strukturierten Form zurückgegeben.

### Rohdaten

```
URL: /election/{id}/{data-format}
```

Die Rohdaten die zur Anzeige der Resultate verwendet werden, sind in den folgenden Formaten verfügbar:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`
XLSX|`/data-xlsx`

Die folgenden Felder sind in allen Formaten enthalten:

Name|Beschreibung
---|---
`election_title`|Titel der Wahl
`election_date`|Das Datum der Wahl (ein ISO 8601 String)
`election_type`|`proporz` falls Proporzwahl, `majorz` falls Majorzwahl
`election_mandates`|Die Anzahl der Sitze.
`election_absolute_majority`|Das absolute Mehr. Nur bei Majorzwahlen.
`election_status`|Zwischenergebnisse (`interim`), Endergebnisse (`final`) oder unbekannt (`unknown`).
`election_counted_entities`|Die Anzahl ausgezählter Gemeinden.
`election_total_entities`|Die Gesamtanzahl an Gemeinden.
`entity_name`|Der Name der Gemeinde
`entity_id`|Die ID der Gemeinde. Der Wert `0` steht für Auslandschweizer.
`entity_elegible_voters`|Die Anzahl Stimmberechtigter der Gemeinde.
`entity_received_ballots`|Die Anzahl abgegebener Stimmzettel der Gemeinde.
`entity_blank_ballots`|Die Anzahl leerer Stimmzettel der Gemeinde.
`entity_invalid_ballots`|Die Anzahl ungültiger Stimmzettel der Gemeinde.
`entity_unaccounted_ballots`|Die Anzahl der ungültigen oder leeren Stimmzettel der Gemeinde.
`entity_accounted_ballots`|Die Anzahl gültiger Stimmzettel der Gemeinde.
`entity_blank_votes`|Die Anzahl leerer Stimmen der Gemeinde.
`entity_invalid_votes`|Die Anzahl ungültiger Stimmen der Gemeinde. `null` falls Proporzwahl.
`entity_accounted_votes`|Die Anzahl gültiger Stimmen der Gemeinde.
`list_name`|Der Name der Liste des Kandidierenden. Nur bei Proporzwahlen.
`list_id`|Die ID der Liste, für welche der Kandidierende kandidiert. Nur bei Proporzwahlen.
`list_number_of_mandates`|Die Anzahl Sitze der Liste. Nur bei Proporzwahlen.
`list_votes`|Die Anzahl der Listenstimmen. Nur bei Proporzwahlen.
`list_connection`|Die ID der Listenverbindung. Nur bei Proporzwahlen.
`list_connection_parent`|Die ID der übergeorndeten Listenverbidnung. Nur bei Proporzwahlen und falls es sich um eine Unterlistenverbindung handelt.
`candidate_family_name`|Der Nachnahme des Kandidierenden.
`candidate_first_name`|Der Vorname des Kandidierenden.
`candidate_id`|Die ID des Kandidierenden.
`candidate_elected`|True, falls der Kandidierenden gewählt wurde.
`candidate_votes`|Die Anzahl Kandidierendenstimmen der Gemeinde.
`panachage_votes_from_list_XX`|Die Anzahl Stimmen von der Liste mit `list_id = XX`. Die `list_id` mit dem Wert `999` steht für die Blankoliste.

Noch nicht ausgezählte Gemeinden sind nicht enthalten.

### Parteiresultate

```
URL: /election/{id}/{data-parties}
```

Die Rohdaten sind als CSV verfügbar. Die folgenden Felder sind enthalten:

Name|Description
---|---
`year`|Das Jahr der Wahl.
`total_votes`|Die Gesamtanzahl der Stimmen der Wahl.
`name`|Der Name der Partei.
`color`|Die Farbe der Partei.
`mandates`|Die Anzahl Mandate der Partei.
`votes`|Die Anzahl Stimmen der Partei.

3 Abstimmungsresultate
----------------------

### Aufbereitete Ergebnisse

```
URL: /vote/{id}/json
```

Es werden dieselben Daten wie in der normalen Ansicht in einer strukturierten Form zurückgegeben.

### Rohdaten

```
URL: /vote/{id}/{data-format}
```

Die Rohdaten die zur Anzeige der Resultate verwendet werden, sind in den folgenden Formaten verfügbar:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`
XLSX|`/data-xlsx`

Die folgenden Felder sind in allen Formaten enthalten:

Name|Beschreibung
---|---
`title`|Titel der Abstimmung.
`date`|Das Datum der Abstimmung (ein ISO 8601 String).
`shortcode`|Internes Kürzel (definiert die Reihenfolge von mehreren Abstimmungen an einem Tag).
`domain`|`federation` für Nationale Abstimmungen, `canton` für Kantonale Abstimmungen
`status`|Zwischenergebnisse (`interim`), Endergebnisse (`final`) oder unbekannt (`unknown`).
`type`|`proposal` (Vorschlag), `counter-proposal` (Gegenvorschlag) or `tie-breaker` (Stichfrage).
`group`|Woher das Resultat kommt. Das kann der Bezirk und die Gemeinde, getrennt mittels eines Schrägstrichs, der Name der Stadt und der Name des Kreises, ebenfalls getrennt mittels eines Schrägstrichts, oder ein einfacher Gemeinde Name sein. All dies hängt vom jeweiligen Kanton ab.
`entity_id`|Die ID der Gemeinde. Der Wert `0` steht für Auslandschweizer.
`counted`|Wahr, wenn das Resultat ausgezählt wurde. Falsch, wenn das Resultat noch nicht bekannt ist (die Werte sind noch nicht korrekt).
`yeas`|Die Anzahl Ja Stimmen
`nays`|Die Anzahl Nein Stimmen
`invalid`|Die Anzahl ungültiger Stimmen
`empty`|Die Anzahl leerer Stimmen
`elegible_voters`|Die Anzahl Stimmberechtigter
