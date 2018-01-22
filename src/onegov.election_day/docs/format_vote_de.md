Format Spezifikation Abstimmungen
=================================

Als Dateiformate werden Dateien akzeptiert, welche von Hand, vom Wahlprogrammen "Wabsti Wahlen und Abstimmungen (VRSG)" oder der Webapplikation selbst generiert werden.

Eine "Gemeinde" kann auch ein Bezirk, ein Wahlkreis etc. sein.

Inhalt
------

1. [Standardformat](#1-standardformat)
2. [OneGov](#2-onegov)
3. [Wabsti](#3-wabsti)
4. [WabstiCExport](#4-wabsticexport)


1 Standardformat
------------------

Pro Abstimmungsvorlage besteht in der Regel eine CSV/Excel Datei. Beinhaltet die Abstimmung jedoch ein Gegenvorschlag und eine Stichfrage, dann müssen drei Dateien geliefert werden: Eine Datei mit den Resultaten der Abstimmung, eine Datei mit den Resultaten des Gegenvorschlags und eine Datei mit den Resultaten der Stichfrage.

### Spalten

Jede Zeile enthält das Resultat einer einzelnen Gemeinde, sofern diese
vollständig ausgezählt wurde. Folgende Spalten werden dabei in der hier
aufgelisteten Reihenfolge erwartet:

Name|Beschreibung
---|---
`ID`|Die BFS-Nummer der Gemeinde zum Zeitpunkt der Abstimmung. Der Wert `0` kann für Auslandslebende verwendet werden.
`Ja Stimmen`|Die Anzahl Ja Stimmen zu der Abstimmung. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Nein Stimmen`|Die Anzahl Nein Stimmen der Abstimmung. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Stimmberechtigte`|Die Anzahl Stimmberechtigter. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Leere Stimmzettel`|Die Anzahl leer eingelegter Stimmzettel. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Ungültige Stimmzettel`|Die Anzahl ungültiger Stimmzettel. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).

### Temporäre Resultate

Gemeinden gelten als noch nicht ausgezählt, falls die Gemeinde nicht in den Resultaten enthalten ist.

### Vorlage

- [vote_standard.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_standard.csv)


2 OneGov
--------

Das Format, welche von der Web-Applikation für den Export verwendet wird, besteht aus einer einzelnen Datei pro Abstimmung. Es gibt für jede Gemeinde und Abstimmungstyp (Vorschlag, Gegenvorschlag, Stichfrage) eine Zeile.

### Spalten

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
`elegible_voters`|Die Anzahl Stimmberechtigter


### Temporäre Resultate

Gemeinden gelten als noch nicht ausgezählt, falls eine der beiden folgenden Bedinungen zutrifft:
- `counted = false`
- die Gemeinde ist nicht in den Resultaten enthalten

Falls der Status
- `interim` ist, gilt die Abstimmung als noch nicht abgeschlossen
- `final` ist, gilt die Abstimmung als abgeschlossen
- `unknown` ist, gilt die Abstimmung als abgeschlossen, falls alle (erwarteten) Gemeinden ausgezählt sind

### Vorlage

- [vote_onegov.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_onegov.csv)


3 Wabsti
--------

Das Format des Wahlprogrammen "Wabsti Wahlen und Abstimmungen (VRSG)" besteht aus einer einzelnen Datei, welche alle Daten für mehrere Abstimmungen enthält. Es gibt für jede Abstimmung und Gemeinde eine Zeile.

### Spalten

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`Vorlage-Nr.`|Eine fortlaufende Nummer für jede Vorlage/Abstimmung. Muss beim Upload Dialog angegeben werden.
`Name`|Der Name der Gemeinde
`BfS-Nr.`|Die BFS-Nummer der Gemeinde. Es kann jeder beliebige Werte für Auslandschweizer verwendet werden, falls `Name = Auslandschweizer`.
`Stimmberechtigte`|Die Anzahl Stimmberechtigter.
`leere SZ`|Die Anzahl leer eingelegter Stimmzettel.
`ungültige SZ`|Die Anzahl ungültiger Stimmzettel.
`Ja`|Die Anzahl Ja Stimmen.
`Nein`|Die Anzahl Nein Stimmen.
`GegenvJa`|Die Anzahl Ja Stimmen zum Gegenvorschlag.
`GegenvNein`| Die Anzahl Nein Stimmen zum Gegenvorschlag.
`StichfrJa`|Die Anzahl Ja Stimmen zur Stichfrage.
`StichfrNein`|Die Anzahl Nein Stimmen zur Stichfrage.
`StimmBet`|Die Stimmbeteilgung in Prozent. Wird verwendet, um zu entscheiden, ob die Gemeinde bereits ausgezählt wurde. Ist die Stimmbeteilgung `0`, wird die Zeile ignoriert (noch nicht ausgezählt).

### Temporäre Resultate

Gemeinden gelten als noch nicht ausgezählt, falls eine der beiden folgenden Bedinungen zutrifft:
- `StimmBet = 0`
- die Gemeinde ist nicht in den Resultaten enthalten

### Vorlage

- [vote_wabsti.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_wabsti.csv)


4 WabstiCExport
---------------

Es wird die Version `2.2` wird unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumenation des Exporter-Programms definiert.
