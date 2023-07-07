# Format Spezifikation Abstimmungen

Als Dateiformate werden Dateien akzeptiert, welche von Hand, vom Wahlprogrammen "Wabsti Wahlen und Abstimmungen (VRSG)" oder der Webapplikation selbst generiert werden.

Eine "Gemeinde" kann auch ein Bezirk, ein Wahlkreis etc. sein.

## Inhalt

<!-- https://atom.io/packages/atom-mdtoc -->
<!-- MDTOC maxdepth:6 firsth1:2 numbering:1 flatten:0 bullets:1 updateOnSave:1 -->

- 1. [Inhalt](#inhalt)
- 2. [Vorbemerkungen](#vorbemerkungen)
   - 2.1. [Einheiten](#einheiten)
- 3. [Formate](#formate)
   - 3.1. [Standardformat](#standardformat)
      - 3.1.1. [Spalten](#spalten)
      - 3.1.2. [Temporäre Resultate](#temporäre-resultate)
      - 3.1.3. [Vorlage](#vorlage)
   - 3.2. [OneGov](#onegov)
      - 3.2.1. [Spalten](#spalten)
      - 3.2.2. [Temporäre Resultate](#temporäre-resultate)
      - 3.2.3. [Vorlage](#vorlage)
   - 3.3. [Wabsti](#wabsti)
      - 3.3.1. [Spalten](#spalten)
      - 3.3.2. [Temporäre Resultate](#temporäre-resultate)
      - 3.3.3. [Vorlage](#vorlage)
   - 3.4. [WabstiCExport](#wabsticexport)
      - 3.4.1. [Ermittlung des Status einer Abstimmung](#ermittlung-des-status-einer-abstimmung)
   - 3.5. [eCH-0252](#ech-0252)

<!-- /MDTOC -->



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
`Ja Stimmen`|Die Anzahl Ja Stimmen zu der Abstimmung. Ist der Text `unbekannt`/`unknown` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Nein Stimmen`|Die Anzahl Nein Stimmen der Abstimmung. Ist der Text `unbekannt`/`unknown` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Stimmberechtigte`|Die Anzahl Stimmberechtigter. Ist der Text `unbekannt`/`unknown` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Leere Stimmzettel`|Die Anzahl leer eingelegter Stimmzettel. Ist der Text `unbekannt`/`unknown` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Ungültige Stimmzettel`|Die Anzahl ungültiger Stimmzettel. Ist der Text `unbekannt`/`unknown` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).

#### Temporäre Resultate

Gemeinden gelten als noch nicht ausgezählt, falls die Gemeinde nicht in den Resultaten enthalten ist.

#### Vorlage

- [vote_standard.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/vote_standard.csv)

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
`expats`|Anzahl Auslandschweizer. Optional.


#### Temporäre Resultate

Gemeinden gelten als noch nicht ausgezählt, falls eine der beiden folgenden Bedingungen zutrifft:
- `counted = false`
- die Gemeinde ist nicht in den Resultaten enthalten

Falls der Status
- `interim` ist, gilt die Abstimmung als noch nicht abgeschlossen
- `final` ist, gilt die Abstimmung als abgeschlossen
- `unknown` ist, gilt die Abstimmung als abgeschlossen, falls alle (erwarteten) Gemeinden ausgezählt sind

#### Vorlage

- [vote_onegov.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/vote_onegov.csv)


### Wabsti

Das Format des Wahlprogrammes "Wabsti Wahlen und Abstimmungen (VRSG)" besteht aus einer einzelnen Datei, welche alle Daten für mehrere Abstimmungen enthält. Es gibt für jede Abstimmung und Gemeinde eine Zeile.

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

- [vote_wabsti.csv](https://github.com/OneGov/onegov-cloud/blob/master/src/onegov/election_day/static/docs/api/templates/vote_wabsti.csv)


### WabstiCExport

Es wird die Version `>= 2.2` unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumentation des Exporter-Programms definiert.

#### Ermittlung des Status einer Abstimmung

In der Format-Spezifikation der Datei `SG_Geschaefte.csv` befinden sich folgende Spalten:

- `Ausmittlungsstand`: Wird vom Benutzer am Wabsti-Client ausgelöst für die gesamte Datenlieferung
- `AnzGdePendent`/`AnzPendentGde`: Indikator, ob die Einzelabstimmung abgeschlossen ist, auch wenn mehrere Abstimmungen in der Datenlieferung sind.

Seit 2020 wird `AnzGdePendent` statt `Ausmittlungsstand` dazu verwendet, um den Status der Gesamtabstimmung zu setzen.
Der Status ist `final` wenn `AnzGdePendent = 0` ist.

Seit 2023 wird `AnzPendentGde` statt `AnzGdePendent` dazu verwendet, um den Status der Gesamtabstimmung zu setzen.


### eCH-0252

Siehe [eCH-0252](https://www.ech.ch/de/ech/ech-0252).
