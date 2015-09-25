# Wahlen & Abstimmungen Webapplikation

## Format Spezifikation Abstimmungen

### Einleitung

Am Abstimmungssonntag werden Resultate zu einzelnen Abstimmungen laufend publiziert. Bei der neuen "Wahlen & Abstimmungen" Webapplikation geschieht dies über ein Webinterface, das CSV oder Excel Dateien mit provisorischen oder definitiven Resultaten entgegennimmt.

Dieses Dokument beschreibt das Format dieser CSV/Excel Dateien.

### Dateiformat

Als Dateiformat werden CSV, XLS oder XLSX Dateien akzeptiert. Bei Excel Dateien ist zu beachten, dass nur das erste Arbeitsblatt berücksichtigt wird. Auch dürfen keine Formeln oder andersweitige Formatierungen im Arbeitsblatt enthalten sein.

Die Dateien bestehen unabhängig vom verwendeten Dateiformat aus einer Kopfzeile und einer beliebigen Anzahl von Resultatzeilen. Die Kopfzeile enthält die Namen der Spalten und ist *zwingend erforderlich*.

Pro Abstimmungsvorlage besteht in der Regel eine CSV/Excel Datei. Beinhaltet die Abstimmung jedoch ein Gegenvorschlag und eine Stichfrage, dann müssen drei Dateien geliefert werden: Eine Datei mit den Resultaten der Abstimmung, eine Datei mit den Resultaten des Gegenvorschlags und eine Datei mit den Resultaten der Stichfrage.

### Felder

Jede Zeile enthält das Resultat einer einzelnen Gemeinde, sofern diese vollständig ausgezählt wurde.
Folgende Felder/Spalten werden dabei in der hier aufgelisteten Reihenfolge erwartet:

**Bezirk**

Der Bezirk in der sich die Gemeinde befindet. Ist die Gemeinde in keinem Bezirk, darf dieses Feld leer sein.
  
**BFS-Nummer**

Die BFS-Nummer der Gemeinde zum Zeitpunkt der Abstimmung.

**Gemeinde**

Der Name der Gemeinde.

**Ja Stimmen**

Die Anzahl Ja Stimmen zu der Abstimmung.

**Nein Stimmen**

Die Anzahl Nein Stimmen der Abstimmung.

**Stimmberechtigte**

Die Anzahl Stimmberechtigter.

**Leere Stimmzettel**

Die Anzahl leer eingelegter Stimmzettel.

**Ungültige Stimmzettel**

Die Anzahl ungültiger Stimmzettel.

### Vorlage

* XLS Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage.xls]()
* CSV Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage.csv]()
* XLSX Vorlage: [https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/vorlage.xlsx]()

### Beispiel

«Schluss mit den Steuerprivilegien für Millionäre (Abschaffung der Pauschalbesteuerung)»

Resultate des Kanton Zug: [https://github.com/OneGov/onegov.election_day/blob/master/docs/steuerprivilegien.csv]()

| Bezirk | BFS-Nummer | Gemeinde    | Ja Stimmen | Nein Stimmen | Stimmberechtigte | Leere Stimmzettel | Ungültige Stimmzettel | 
|--------|------------|-------------|------------|--------------|------------------|-------------------|-----------------------| 
|        | 1711       | Zug         | 3515       | 6458         | 16914            | 123               | 123                   | 
|        | 1706       | Oberägeri   | 575        | 1422         | 3639             | 123               | 123                   | 
|        | 1709       | Unterägeri  | 901        | 1930         | 5325             | 123               | 123                   | 
|        | 1704       | Menzingen   | 435        | 1126         | 2960             | 123               | 123                   | 
|        | 1701       | Baar        | 2454       | 4967         | 13982            | 123               | 123                   | 
|        | 1702       | Cham        | 1741       | 3525         | 9768             | 123               | 123                   | 
|        | 1703       | Hünenberg   | 1063       | 2375         | 5925             | 123               | 123                   | 
|        | 1708       | Steinhausen | 1127       | 2178         | 5993             | 123               | 123                   | 
|        | 1707       | Risch       | 1008       | 2151         | 6115             | 123               | 123                   | 
|        | 1710       | Walchwil    | 369        | 985          | 2057             | 123               | 123                   | 
|        | 1705       | Neuheim     | 193        | 529          | 1299             | 123               | 123                   | 