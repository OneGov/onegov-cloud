# Format Spezifikation Abstimmungen

Als Dateiformate werden Dateien akzeptiert, welche von Hand, vom Wahlprogrammen "Wabsti Wahlen und Abstimmungen (VRSG)" oder der Webapplikation selbst generiert werden.

Eine "Gemeinde" kann auch ein Bezirk, ein Wahlkreis etc. sein.

## Inhalt

<!-- TOC updateonsave:false -->

- [Format Spezifikation Abstimmungen](#format-spezifikation-abstimmungen)
    - [Inhalt](#inhalt)
    - [Vorbemerkungen](#vorbemerkungen)
        - [Einheiten](#einheiten)
    - [Formate](#formate)
        - [eCH-0252](#ech-0252)
        - [OneGov](#onegov)
            - [Spalten](#spalten)
            - [Temporäre Resultate](#tempor%C3%A4re-resultate)
            - [Vorlage](#vorlage)
        - [WabstiCExport](#wabsticexport)
            - [Ermittlung des Status einer Abstimmung](#ermittlung-des-status-einer-abstimmung)

<!-- /TOC -->



## Vorbemerkungen

### Einheiten

Eine Einheit entspricht einer Gemeinde (kantonale Instanzen, kommunale Instanzen ohne Stadtteilen) oder einem Stadtteil (kommunale Instanzen mit Stadtteilen).

## Formate

### eCH-0252

Siehe [eCH-0252](https://www.ech.ch/de/ech/ech-0252).


### OneGov

Das Format, welche von der Web-Applikation für den Export verwendet wird, besteht aus einer einzelnen Datei pro Abstimmung. Es gibt für jede Gemeinde und Abstimmungstyp (Vorschlag, Gegenentwurf/Gegenvorschlag, Stichfrage) eine Zeile.

#### Spalten

Es werden folgende Spalten ausgewertet und sollten vorhanden sein:

Name|Beschreibung
---|---
`status`|`unknown`, `interim` or `final`.
`type`|`proposal` (Vorschlag), `counter-proposal` (Gegenentwurf/Gegenvorschlag) or `tie-breaker` (Stichfrage).
`entity_id`|Die ID der Gemeinde. Der Wert `0` steht für Auslandschweizer.
`counted`|Wahr wenn das Resultat ausgezählt wurde. Falsch wenn das Resultat noch nicht bekannt ist (die Werte sind noch nicht korrekt).
`yeas`|Die Anzahl Ja Stimmen
`nays`|Die Anzahl Nein Stimmen
`invalid`|Die Anzahl ungültiger Stimmen
`empty`|Die Anzahl leerer Stimmen
`eligible_voters`|Die Anzahl Stimmberechtigter
`expats`|Anzahl Auslandschweizer. Optional.
`received`|Anzahl eingegangener Stimmzettel. Optional.


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



### WabstiCExport

Es wird die Version `>= 2.2` unterstützt. Die verschiedenen Spalten der verschiedenen Dateien sind in der Dokumentation des Exporter-Programms definiert.

#### Ermittlung des Status einer Abstimmung

In der Format-Spezifikation der Datei `SG_Geschaefte.csv` befinden sich folgende Spalten:

- `Ausmittlungsstand`: Wird vom Benutzer am Wabsti-Client ausgelöst für die gesamte Datenlieferung
- `AnzGdePendent`/`AnzPendentGde`: Indikator, ob die Einzelabstimmung abgeschlossen ist, auch wenn mehrere Abstimmungen in der Datenlieferung sind.

Seit 2020 wird `AnzGdePendent` statt `Ausmittlungsstand` dazu verwendet, um den Status der Gesamtabstimmung zu setzen.
Der Status ist `final` wenn `AnzGdePendent = 0` ist.

Seit 2023 wird `AnzPendentGde` statt `AnzGdePendent` dazu verwendet, um den Status der Gesamtabstimmung zu setzen.


