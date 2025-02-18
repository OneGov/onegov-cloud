# Einsatzberichte der Feuerwehr Winterthur: Open Data

## Nutzungsbedingungen

Freie Nutzung. Quellenangabe ist Pflicht.

- Sie dürfen diesen Datensatz für nicht kommerzielle Zwecke nutzen.
- Sie dürfen diesen Datensatz für kommerzielle Zwecke nutzen.
- Eine Quellenangabe ist Pflicht (Autor, Titel und Link zum Datensatz).

## Einsatzberichte der Feuerwehr Winterthur
Die Einsatzberichte der Feuerwehr Winterthur sind im JSON- und CSV-Format
verfügbar.

```
URL /mission-reports/json
URL /mission-reports/csv
```

### Datenfelder

Datensatz:

| Name                    | Typ           | Beschreibung                            |
|-------------------------|---------------|-----------------------------------------|
| `name`                  | string        | Name des Datensatzes `Mission Reports`   |
| `report_count`          | int           | Anzahl der Einsatzberichte im Datensatz |
| `reports`               | list[report] | Liste der Einsatzberichte               |


Einsatzbericht (`report`):

| Name                    | Typ          | Beschreibung                                      |
|-------------------------|--------------|---------------------------------------------------|
| `date`                  | string       | Datum des Einsatzes im iso-Format                 |
| `alarm`                 | string       | Alarmzeit                                         |
| `duration`              | string       | Dauer des Einsatzes im Format `1.2h`              |
| `nature`                | string       | Beschreibung des Einsatzes                        |
| `mission_type`          | string       | Art des Einsatzes (`single`, `multiple`)          |
| `mission_count`         | int          | Anzahl der Einsätze falls `mission_type==multi`   |
| `vehicles`              | list[string] | Liste der eingesetzten Fahrzeuge                  |
| `vehicle_icons`         | list[string] | Liste der Icons der Einsatzfahrzeuge im Einsatz als URL |
| `location`              | string       | Einsatzort                                        |
| `personnel_active`      | int          | Anzahl der aktiven Einsatzkräfte                  |
| `personnel_backup`      | int          | Anzahl der Einsatzkräfte nicht im Einsatz (Backup) |
| `civil_defense_involved`| bool         | Zivilschutz involviert (true, false)              |

### Beispiel JSON
```json
{
  "name": "Mission Reports",
  "report_count": 1,
  "reports": [
    "date": "2021-01-01",
    "alarm": "8:30",
    "duration": "1.3h",
    "nature": "Containerbrand",
    "mission_type": "single",
    "mission_count": 2,
    "vehicles": ["Tanklöschfahrzeug TLF"],
    "vehicle_icons": ["http://../storage/345e..db80"],
    "location": "Museumsstrasse, Winterthur",
    "personnel_active": 5,
    "personnel_backup": 4,
    "civil_defense_involved": false,
  ]
```

### Beispiel CSV
Die erste Zeile enthält die Spaltennamen. Die weiteren Zeilen enthalten die einzelnen Einsatzberichte.
```
date,alarm,duration,nature,mission_type,mission_count,vehicles,vehicles_icons,location,personnel_active,personnel_backup,civil_defence_involved
12-11-2024,08:30,2.4h,Fehlalarm Rauchmelder,single,1,Drehleiter DL,http://../storage/345e..db80,Luzern,3,8,False
31-10-2024,12:01,4h,Schwehlbrand im Dachgeschoss,multi,2,"Drehleiter DL, Drehleiter DL, Tanklöschfahrzeug TLF","http://../storage/345e..db80, http://. ./storage/345e..db80, http://../storage/15e6..0530","Pilatusstrasse 3, 6003 Luzern",6,2,False
```

### URL Parameter
Mit den folgenden Parametern können die Einsatzberichte gefiltert werden.

| Parameter | Typ  | Beschreibung                                                                                                    |
|-----------|------|-----------------------------------------------------------------------------------------------------------------|
| None      | -    | Wenn keine Parameter angegeben werden, werden alle Einsatzberichte des aktuellen Kalenderjahres zurückgegeben. |
| `all`     | bool | Wenn `true`, werden alle Einsatzberichte zurückgegeben.                                                         |
| `year`    | int  | Das Jahr, für welches die Einsatzberichte gefiltert werden sollen.                                              |

URL Beispiele:
```
URL /mission-reports/json
URL /mission-reports/json?all=true
URL /mission-reports/json?year=2023

URL /mission-reports/csv
URL /mission-reports/csv?all=true
URL /mission-reports/csv?year=2024
```

