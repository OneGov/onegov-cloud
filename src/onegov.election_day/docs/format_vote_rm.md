# Format Specification Votes

Als Dateiformate werden Dateien akzeptiert, welche von Hand, vom Wahlprogrammen "Wabsti Wahlen und Abstimmungen (VRSG)" oder der Webapplikation selbst generiert werden.

Ina "vischnanca" po er esser in district, in circul electoral e.u.v.

## Cuntegn

<!-- TOC START min:1 max:4 link:true update:true -->
- [Format Specification Votes](#format-specification-votes)
  - [Cuntegn](#cuntegn)
  - [Vorbemerkungen](#vorbemerkungen)
    - [Einheiten](#einheiten)
  - [Formate](#formate)
    - [Standard format](#standard-format)
      - [Colonnas](#colonnas)
      - [Resultats temporars](#resultats-temporars)
      - [Project](#project)
    - [OneGov](#onegov)
    - [Colonnas](#colonnas-1)
      - [Resultats temporars](#resultats-temporars-1)
      - [Project](#project-1)
    - [Wabsti](#wabsti)
      - [Colonnas](#colonnas-2)
      - [Resultats temporars](#resultats-temporars-2)
      - [Project](#project-2)
    - [WabstiCExport](#wabsticexport)

<!-- TOC END -->


## Vorbemerkungen

### Einheiten

Eine Einheit entspricht einer Gemeinde (kantonale Instanzen, kommunale Instanzen ohne Stadtteilen) oder einem Stadtteil (kommunale Instanzen mit Stadtteilen).

## Formate

### Standardformat

Pro Abstimmungsvorlage besteht in der Regel eine CSV/Excel Datei. Beinhaltet die Abstimmung jedoch ein Gegenvorschlag und eine Stichfrage, dann müssen drei Dateien geliefert werden: Eine Datei mit den Resultaten der Abstimmung, eine Datei mit den Resultaten des Gegenvorschlags und eine Datei mit den Resultaten der Stichfrage.

#### Colonnas

Jede Zeile enthält das Resultat einer einzelnen Gemeinde, sofern diese vollständig ausgezählt wurde. Folgende Spalten werden dabei in der hier aufgelisteten Reihenfolge erwartet:

Num|Descripziun
---|---
`ID`|Die BFS-Nummer der Gemeinde zum Zeitpunkt der Abstimmung. Der Wert `0` kann für Auslandslebende verwendet werden.
`Ja Stimmen`|Die Anzahl Ja Stimmen zu der Abstimmung. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Nein Stimmen`|Die Anzahl Nein Stimmen der Abstimmung. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Stimmberechtigte`|Die Anzahl Stimmberechtigter. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Leere Stimmzettel`|Die Anzahl leer eingelegter Stimmzettel. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).
`Ungültige Stimmzettel`|Die Anzahl ungültiger Stimmzettel. Ist der Text `unbekannt` eingetragen, wird die Zeile ignoriert (noch nicht ausgezählt).

#### Resultats temporars

Gemeinden gelten als noch nicht ausgezählt, falls die Gemeinde nicht in den Resultaten enthalten ist.

#### Project

- [vote_standard.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_standard.csv)

### OneGov

Das Format, welche von der Web-Applikation für den Export verwendet wird, besteht aus einer einzelnen Datei pro Abstimmung. Es gibt für jede Gemeinde und Abstimmungstyp (Vorschlag, Gegenvorschlag, Stichfrage) eine Zeile.

### Colonnas

Las suandantas colonnas vegnan evaluadas e ston almain esser avant maun:

Num|Descripziun
---|---
`status`|`unknown`, `interim` or `final`.
`type`|`proposal` (proposta), `counter-proposal` (cuntraproposta) or "tie-breaker" (dumonda decisiva).
`entity_id`|La ID da la vischnanca/dal lieu. A value `0` represents the expats.
`counted`|Gist, sch'il resultat è vegnì eruì. Fauss, sch'il resultat n'è anc betg enconuschent (las valurs n'èn anc betg correctas).
`yeas`|Il dumber da las vuschs affirmativas
`nays`|Il dumber da las vuschs negativas
`invalid`|Il dumber da las vuschs nunvalaivlas
`empty`|Il dumber da las vuschs vidas
`eligible_voters`|Il dumber da las persunas cun dretg da votar


#### Resultats temporars

Gemeinden gelten als noch nicht ausgezählt, falls eine der beiden folgenden Bedingungen zutrifft:
- `counted = false`
- die Gemeinde ist nicht in den Resultaten enthalten

Falls der Status
- `interim` ist, gilt die Abstimmung als noch nicht abgeschlossen
- `final` ist, gilt die Abstimmung als abgeschlossen
- `unknown` ist, gilt die Abstimmung als abgeschlossen, falls alle (erwarteten) Gemeinden ausgezählt sind

#### Project

- [vote_onegov.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_onegov.csv)


### Wabsti

The format of the "Wabsti Elections and Referenda (VRSG)" election program consists of a single file which contains all the data for many referenda. There is a line for every referendum and municipality.

#### Colonnas

Las suandantas colonnas vegnan evaluadas e ston almain esser avant maun:
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

#### Resultats temporars

Gemeinden gelten als noch nicht ausgezählt, falls eine der beiden folgenden Bedingungen zutrifft:
- `StimmBet = 0`
- die Gemeinde ist nicht in den Resultaten enthalten

#### Project

- [vote_wabsti.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/templates/vote_wabsti.csv)


### WabstiCExport

Es wird die Version `>= 2.2` unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumentation des Exporter-Programms definiert.
