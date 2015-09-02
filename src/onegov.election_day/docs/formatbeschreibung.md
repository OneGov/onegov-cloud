# Wahlen & Abstimmungen Webapplikation

## Format Spezifikation Abstimmungen

### Einleitung

Am Abstimmungssonntag werden Resultate zu einzelnen Abstimmungen laufend publiziert. Bei der neuen Wahlen & Abstimmungen Webapplikation geschieht dies über ein Webinterface, das CSV oder Excel Dateien mit laufenden oder definitiven Resultaten entgegennimmt.

Dieses Dokument beschreibt das Format dieser CSV/Excel Dateien.

### Dateiformat

Als Dateiformat werden CSV, XLS oder XLSX Dateien akzeptiert. Bei Excel Dateien ist zu beachten das nur das erste Arbeitsblatt berücksichtigt wird. Auch dürfen keine Formeln oder andersweitige Formatierungen gemacht werden.

Die Dateien bestehen unabhängig vom verwendeten Dateiformat aus einer Kopfzeile und einer beliebigen Anzahl von Resultatzeilen. Die Kopfzeile enthält die Namen der Spalten und ist *nicht* optional.

Pro Abstimmungsvorlage besteht in der Regel eine CSV/Excel Datei. Gehört zu der Abstimmung jedoch ein Gegenvorschlag und eine Stichfrage, dann müssen drei Dateien geliefert werden. Eine Datei mit den Resultaten der Abstimmung, eine Datei mit den Resultaten des Gegenvorschlags und eine Datei mit den Resultaten der Stichfrage.

### Felder

Jede Zeile enthält das Resultat einer einzigen Gemeinde, sofern diese vollständig ausgezählt wurde.
Folgende Felder/Spalten werden dabei in der hier gegebenen Reihenfolge erwartet:

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

**Eingelegte Stimmzettel**

Die Anzahl eingelegter Stimmzettel (inkl. ungültiger Stimmzettel).

### Vorlage

* XLS Vorlage: [https://github.com/OneGov/onegov.election_day/docs/vorlage.xls]()
* CSV Vorlage: [https://github.com/OneGov/onegov.election_day/docs/vorlage.csv]()
* XLSX Vorlage: [https://github.com/OneGov/onegov.election_day/docs/vorlage.xlsx]()

### Beispiel

«Schluss mit den Steuerprivilegien für Millionäre (Abschaffung der Pauschalbesteuerung)»

Resultate des Kanton Zug: 
[https://github.com/OneGov/onegov.election_day/docs/steuerprivilegien.csv]()
