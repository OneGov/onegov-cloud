Wahlen & Abstimmungen: Open Data
================================

Nutzungsbedingungen
-------------------

Freie Nutzung. Quellenangabe ist Pflicht.

- Sie dürfen diesen Datensatz für nicht kommerzielle Zwecke nutzen.
- Sie dürfen diesen Datensatz für kommerzielle Zwecke nutzen.
- Eine Quellenangabe ist Pflicht (Autor, Titel und Link zum Datensatz).

Einleitung
----------

Für jede wichtige Seite gibt es eine entsprechende JSON-Alternative. Alle Antworten enthalten den `Last-Modified` HTTP-Header, welcher Auskunft über den Zeitpunkt der letzten Änderung gibt (z. B., wann zum letzten Mal Ergebnisse einer Wahl oder Abstimmung hochgeladen wurden).

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

Die auf der Startseite und den Archivseiten dargestellten Ergebnisse sind im JSON-Format verfügbar. Die Daten enthalten neben einigen globalen Informationen für jede Wahl / Abstimmung die folgenden Informationen:

Name|Beschreibung
---|---
`type`|`election` für Wahlen, `election_compound` für verbundene Wahlen, `vote` für Abstimmungen.
`title`|Ein Objekt mit den übersetzten Titeln.
`date`|Das Datum (ISO 8601).
`domain`|Einflussbereich (Bund, Kanton, ...).
`url`|Ein Link zur Detailansicht.
`completed`|Wahr, falls die Abstimmung oder Wahl abgeschlossen ist.
`progress`|Ein Objekt, welches die Anzahl ausgezählter Gemeinden/Wahlen (`counted`) und die Gesamtzahl an Gemeinden/Wahlen (`total`) enthält.
`last_modified`|Zeitpunkt der letzten Änderung (ISO 8601).
`turnout`|Stimm-/Wahlbeteiligung in Prozent.

Abstimmungsresultate enthalten die folgenden zusätzlichen Informationen:

Name|Beschreibung
---|---
`answer`|Das Abstimmungsresultat: `accepted` (angenommen), `rejected` (abgelehnt), `proposal` (Initiative) oder `counter-proposal` (Gegenvorschlag/Gegenentwurf).
`yeas_percentage`|Ja-Stimmen in Prozent.
`nays_percentage`|Nein-Stimmen in Prozent.
`local` (*optional*)|Eidgenössische und kantonale Abstimmungen innerhalb kommunaler Instanzen können zusätzlich die Resultate dieser Gemeinde enthalten als zusätzliches Objekt mit den Feldern `answer`, `yeas_percentage` and `nays_percentage`.

Wahlresultate enthalten die folgenden zusätzlichen Informationen:

Name|Beschreibung
---|---
`elected`|Liste mit den gewählten Kandidierenden.

Verbundene Wahlen enthalten die folgenden zusätzlichen Informationen:

Name|Beschreibung
---|---
`elected`|Liste mit den gewählten Kandidierenden.
`elections`|Liste mit Links zu den Wahlen.

2 Wahlresultate
---------------

### Aufbereitete Ergebnisse

```
URL: /election/{id}/json
```

Es werden dieselben Daten wie in der normalen Ansicht in einer strukturierten Form zurückgegeben.

### Rohdaten

#### Kandidierendenresultate

```
URL: /election/{id}/data-{format}
```

Die Rohdaten der Kandidierenden sind in den folgenden Formaten verfügbar:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`

Die folgenden Felder sind in allen Formaten enthalten:

Name|Beschreibung
---|---
`election_id`|ID der Wahl. Wird in der URL verwendet.
`election_title_{locale}`|Übersetzter Titel, z. B. `title_de_ch` für den deutschen Titel.
`election_short_title_{locale}`|Übersetzter Kurztitel, z. B. `title_de_ch` für den deutschen Kurztitel.
`election_date`|Das Datum der Wahl (ein ISO 8601 String)
`election_domain`|national (`federation`), kantonal (`canton`), regional (`region`) oder kommunal (`municipality`)
`election_type`|Proporzwahl (`proporz`) oder Majorzwahl (`majorz`)
`election_mandates`|Die Anzahl der Mandate/Sitze.
`election_absolute_majority`|Das absolute Mehr. Nur bei Majorzwahlen.
`election_status`|Zwischenergebnisse (`interim`), Endergebnisse (`final`) oder unbekannt (`unknown`).
`entity_id`|Die ID der Gemeinde. Der Wert `0` steht für Auslandschweizer.
`entity_name`|Der Name der Gemeinde.
`entity_district`|Wahlkreis/Bezirk/Region der Gemeinde.
`entity_counted`|`True`, wenn das Resultat ausgezählt wurde.
`entity_eligible_voters`|Die Anzahl Stimmberechtigter der Gemeinde.
`entity_expats`|Anzahl stimmberechtigte Auslandschweizer der Gemeinde.
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
`list_color`|Die Farbe der Liste als Hexadezimalwert, z.B. `#a6b784`. Nur bei Proporzwahlen.
`list_number_of_mandates`|Die Anzahl Mandate der Liste. Nur bei Proporzwahlen.
`list_votes`|Die Anzahl der Listenstimmen. Nur bei Proporzwahlen.
`list_connection`|Die ID der Listenverbindung. Nur bei Proporzwahlen.
`list_connection_parent`|Die ID der übergeordneten Listenverbidnung. Nur bei Proporzwahlen und falls es sich um eine Unterlistenverbindung handelt.
`list_panachage_votes_from_list_XX`|Die Anzahl Listenstimmen von der Liste mit `list_id = XX`. Die `list_id` mit dem Wert `999` steht für die Blankoliste. Enthält keine Stimmen aus der eigenen Liste.
`candidate_family_name`|Der Nachnahme des Kandidierenden.
`candidate_first_name`|Der Vorname des Kandidierenden.
`candidate_id`|Die ID des Kandidierenden.
`candidate_elected`|Wahr, falls der Kandidierenden gewählt wurde.
`candidate_party`|Der Name der Partei.
`candidate_party_color`|Die Farbe der Partei als Hexadezimalwert, z.B. `#a6b784`.
`candidate_gender`|Das Geschlecht des Kandidierenden: `female` (weiblich), `male` (männlich) oder `undetermined` (unbestimmt).
`candidate_year_of_birth`|Der Jahrgang des Kandidierenden.
`candidate_votes`|Die Anzahl Kandidierendenstimmen der Gemeinde.
`candidate_panachage_votes_from_list_XX`|Die Anzahl Kandidierendenstimmen von der Liste mit `list_id = XX`. Die `list_id` mit dem Wert `999` steht für die Blankoliste.

Verbundene Wahlen enthalten die folgenden zusätzlichen Informationen:

Name|Description
---|---
`compound_id`|ID des Verbundes. Wird in der URL verwendet.
`compound_title_{locale}`|Übersetzter Titel, z. B. `title_de_ch` für den deutschen Titel.
`compound_short_title_{locale}`|Übersetzter Kurztitel, z. B. `title_de_ch` für den deutschen Kurztitel.
`compound_date`|Das Datum der Wahl (ein ISO 8601 String)
`compound_mandates`|Die Gesamtanzahl der Mandate/Sitze.

Noch nicht ausgezählte Gemeinden sind nicht enthalten.

#### Parteiresultate

```
URL: /election/{id}/data-parties-{format}
```

Die Rohdaten der Parteien sind in den folgenden Formaten verfügbar:

Format|URL
---|---
JSON|`/data-parties-json`
CSV|`/data-parties-csv`

Die folgenden Felder sind in allen Formaten enthalten:


Name|Description
---|---
`domain`|Der Einflussbereich, für den die Zeile gilt.
`domain_segment`|Die Einheit des Einflussbereichs, für die die Zeile gilt.
`year`|Das Jahr der Wahl.
`total_votes`|Die Gesamtanzahl der Stimmen der Wahl.
`name`|Der Name der Partei in der Standardsprache.
`name_{locale}`|Übersetzter Name der Partei, z. B. `name_de_ch` für den deutschen Namen.
`id`|ID der Partei (beliebige Zahl).
`color`|Die Farbe der Partei als Hexadezimalwert, z.B. `#a6b784`.
`mandates`|Die Anzahl Mandate der Partei.
`votes`|Die Anzahl Stimmen der Partei.
`voters_count`|Wählerzahlen. Die kumulierte Anzahl Stimmen pro Gesamtanzahl Mandate pro Wahl. Nur für verbundene Wahlen.
`voters_count_percentage`|Wählerzahlen (prozentual)). Die kumulierte Anzahl Stimmen pro Gesamtanzahl Mandate pro Wahl (prozentual). Nur für verbundene Wahlen.
`panachage_votes_from_{XX}`|Die Anzahl Stimmen von der Partei mit `id = XX`. Die `id` mit dem Wert `999` steht für die Stimmen aus der Blankoliste.

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

Die Rohdaten, die zur Anzeige der Resultate verwendet werden, sind in den folgenden Formaten verfügbar:

Format|URL
---|---
JSON|`/data-json`
CSV|`/data-csv`

Die folgenden Felder sind in den Formaten `JSON` und `CSV` enthalten:

Name|Beschreibung
---|---
`id`|ID der Abstimmung. Wird in der URL verwendet.
`title_{locale}`|Übersetzter Titel, z. B. `title_de_ch` für den deutschen Titel.
`short_title_{locale}`|Übersetzter Kurztitel, z. B. `title_de_ch` für den deutschen Kurztitel.
`date`|Das Datum der Abstimmung (eine ISO-8601-Zeichenkette).
`shortcode`|Internes Kürzel (definiert die Reihenfolge von mehreren Abstimmungen an einem Tag).
`domain`|`federation` für nationale Abstimmungen, `canton` für kantonale Abstimmungen
`status`|Zwischenergebnisse (`interim`), Endergebnisse (`final`) oder unbekannt (`unknown`).
`answer`|Das Abstimmungsresultat: `accepted` (angenommen), `rejected` (abgelehnt), `proposal` (Initiative) oder `counter-proposal` (Gegenvorschlag/Gegenentwurf).
`type`|Typ: `proposal` (Vorschlag), `counter-proposal` (Gegenvorschlag/Gegenentwurf) oder `tie-breaker` (Stichfrage).
`ballot_answer`| Das Abstimmungsresultat nach Typ: `accepted` (angenommen) oder `rejected` (abgelehnt) für `type=proposal` (Vorschlag) und `type=counter-proposal` (Gegenvorschlag/Gegenentwurf);
`proposal` (Initiative) oder `counter-proposal` (Gegenvorschlag/Gegenentwurf) für `type=tie-breaker` (Stichfrage).
`district`|Wahlkreis/Bezirk/Region der Gemeinde.
`name`|Der Name der Gemeinde.
`entity_id`|Die ID der Gemeinde. Der Wert `0` steht für Auslandschweizer.
`counted`|Wahr, wenn das Resultat ausgezählt wurde. Falsch, wenn das Resultat noch nicht bekannt ist (die Werte sind noch nicht korrekt).
`yeas`|Die Anzahl Ja-Stimmen
`nays`|Die Anzahl Nein-Stimmen
`invalid`|Die Anzahl ungültiger Stimmen
`empty`|Die Anzahl leerer Stimmen
`eligible_voters`|Die Anzahl Stimmberechtigter
`expats`|Anzahl stimmberechtigte Auslandschweizer der Gemeinde.

4 Sitemap
---------

```
URL: /sitemap.xml
```

Gibt eine Sitemap im XML-Format zurück (https://www.sitemaps.org/protocol.html)

```
URL: /sitemap.json
```

Gibt die Sitemap als JSON zurück.
