# Format Spezifikation Abstimmungen

Als Dateiformate werden Dateien akzeptiert, welche von Hand, vom Wahlprogrammen "Wabsti Wahlen und Abstimmungen (VRSG)" oder der Webapplikation selbst generiert werden.

Eine "Gemeinde" kann auch ein Bezirk, ein Wahlkreis etc. sein.

## Inhalt

<!-- TOC START min:1 max:4 link:true update:true -->
- [Format Spezifikation Abstimmungen](#format-spezifikation-abstimmungen)
  - [Inhalt](#inhalt)
  - [Vorbemerkungen](#vorbemerkungen)
    - [Einheiten](#einheiten)
  - [Formate](#formate)
    - [Standardformat](#standardformat)
      - [Spalten](#spalten)
      - [Temporäre Resultate](#temporre-resultate)
      - [Vorlage](#vorlage)
    - [OneGov](#onegov)
      - [Spalten](#spalten-1)
      - [Temporäre Resultate](#temporre-resultate-1)
      - [Vorlage](#vorlage-1)
    - [Wabsti](#wabsti)
      - [Spalten](#spalten-2)
      - [Temporäre Resultate](#temporre-resultate-2)
      - [Vorlage](#vorlage-2)
    - [WabstiCExport](#wabsticexport)

<!-- TOC END -->



## Vorbemerkungen

### Einheiten

Eine Einheit entspricht einer Gemeinde (kantonale Instanzen, kommunale Instanzen ohne Stadtteilen) oder einem Stadtteil (kommunale Instanzen mit Stadtteilen).

## Formate

### Standardformat

Pro Abstimmungsvorlage besteht in der Regel eine CSV/Excel Datei. Beinhaltet die Abstimmung jedoch ein Gegenvorschlag und eine Stichfrage, dann müssen drei Dateien geliefert werden: Eine Datei mit den Resultaten der Abstimmung, eine Datei mit den Resultaten des Gegenvorschlags und eine Datei mit den Resultaten der Stichfrage.

#### Spalten

Jede Zeile enthält das Resultat einer einzelnen Gemeinde, sofern diese vollständig ausgezählt wurde. Folgende Spalten werden dabei in der hier aufgelisteten Reihenfolge erwartet:

Name|Beschreibung
---|---
`ID`|Die BFS-Nummer der Gemeinde zum Zeitpunkt der Abstimmung. Der Wert `0` kann für Auslandslebende verwendet werden.
`Ja Stimmen`|Die Anzahl Ja Stimmen zu der Abstimmung. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Nein Stimmen`|Die Anzahl Nein Stimmen der Abstimmung. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Stimmberechtigte`|Die Anzahl Stimmberechtigter. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Leere Stimmzettel`|Die Anzahl leer eingelegter Stimmzettel. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Ungültige Stimmzettel`|Die Anzahl ungültiger Stimmzettel. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).

#### Temporäre Resultate

Gemeinden gelten als noch nicht ausgezählt, falls die Gemeinde nicht in den Resultaten enthalten ist.

#### Vorlage

- [vote_standard.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_standard.csv)

### OneGov

Das Format, welche von der Web-Applikation für den Export verwendet wird, besteht aus einer einzelnen Datei pro Abstimmung. Es gibt für jede Gemeinde und Abstimmungstyp (Vorschlag, Gegenvorschlag, Stichfrage) eine Zeile.

#### Spalten

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`status`|`unknown`, `interim` or `final`.
`type`|`proposal` (Vorschlag), `counter-proposal` (Gegenvorschlag) or `tie-breaker` (Stichfrage).
`entity_id`|Die ID der Gemeinde. Der Wert `0` steht für Auslandschweizer.
`counted`|Wahr wenn das Resultat ausgezählt wurde. Falsch wenn das Resultat noch nicht bekannt ist (die Werte sind noch nicht korrekt).
`yeas`|Die Anzahl Ja Stimmen
`nays`|Die Anzahl Nein Stimmen
`invalid`|Die Anzahl ungültiger Stimmen
`empty`|Die Anzahl leerer Stimmen
`eligible_voters`|Die Anzahl Stimmberechtigter


#### Temporäre Resultate

Gemeinden gelten als noch nicht ausgezählt, falls eine der beiden folgenden Bedingungen zutrifft:
- `counted = false`
- die Gemeinde ist nicht in den Resultaten enthalten

Falls der Status
- `interim` ist, gilt die Abstimmung als noch nicht abgeschlossen
- `final` ist, gilt die Abstimmung als abgeschlossen
- `unknown` ist, gilt die Abstimmung als abgeschlossen, falls alle (erwarteten) Gemeinden ausgezählt sind

#### Vorlage

- [vote_onegov.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_onegov.csv)


### Wabsti

Das Format des Wahlprogrammen "Wabsti Wahlen und Abstimmungen (VRSG)" besteht aus einer einzelnen Datei, welche alle Daten für mehrere Abstimmungen enthält. Es gibt für jede Abstimmung und Gemeinde eine Zeile.

#### Spalten

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:
- `Vorlage-Nr.`
- `Name`
- `BfS-Nr.`
- `Stimmberechtigte`
- `leere SZ`
- `ungültige SZ`
- `Ja`
- `Nein`
- `GegenvJa`
- `GegenvNein`
- `StichfrJa`
- `StichfrNein`
- `StimmBet`

#### Temporäre Resultate

Gemeinden gelten als noch nicht ausgezählt, falls eine der beiden folgenden Bedingungen zutrifft:
- `StimmBet = 0`
- die Gemeinde ist nicht in den Resultaten enthalten

#### Vorlage

- [vote_wabsti.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_wabsti.csv)


### WabstiCExport

Es wird die Version `>= 2.2` unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumentation des Exporter-Programms definiert.
