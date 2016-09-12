# Spécifications de format des élections

En ce qui concerne les formats de fichiers, les fichiers XLS et XLSX sont acceptés, ils sont générés par les programmes électoraux « élections (SESAM) » et « Wabsti élections et votes (VRSG) », ou par l'application web elle-même. Si une table est créée manuellement, le format de l'application web sera alors le plus facile.

«Municipalité» fait référence à un district, une circonscription électorale, etc.

## Contenu

[SESAM Majorz](#sesam-majorz)

[SESAM Proporz](#sesam-proporz)

[Wabsti Majorz](#wabsti-majorz)

[Wabsti Proporz](#wabsti-proporz)

[OneGov](#onegov)


## SESAM Majorz

Le format d'exportation SESAM contient directement toutes les données requises. Il y a une ligne par candidat et municipalité.

### Colonnes

Les colonnes suivantes seront évaluées et on devrait avoir au moins celles-ci :

- **Anzahl Sitze** (Nombre de places)
- **Wahlkreis-Nr** (Numéro de circonscription électorale)
- **Anzahl Gemeinden** (Nombre de municipalités)
- **Stimmberechtigte** (Autorisé à voter)
- **Wahlzettel** (Bulletins)
- **Ungültige Wahlzettel** (Bulletins non valides)
- **Leere Wahlzettel** (Bulletins vides)
- **Leere Stimmen** (Votes vides)
- **Ungueltige Stimmen** (Votes non valides)
- **Kandidaten-Nr** (Numéro de candidat)
- **Gewaehlt** (Élu)
- **Name** (Nom)
- **Vorname** (Prénom)
- **Stimmen** (Votes)

### Résultats temporaires

On juge que l'élection n'est pas comptée si la quantité de municipalités comptées dans « Nombre de municipalités » ne correspond pas au nombre total de municipalités. Les municipalités qui ne sont pas encore comptées ne sont pas incluses dans les données.

### Modèle

[election_sesam_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_sesam_majorz.csv)

## SESAM Proporz

Le format d'exportation SESAM contient directement toutes les données requises. Il y a une ligne par candidat et municipalité.

### Colonnes

Les colonnes suivantes seront évaluées et on devrait avoir au moins celles-ci :

- **Anzahl Sitze** (Nombre de places)
- **Wahlkreis-Nr** (Numéro de circonscription électorale)
- **Stimmberechtigte** (Autorisé à voter)
- **Wahlzettel** (Bulletins)
- **Ungültige Wahlzettel** (Bulletins non valides)
- **Leere Wahlzettel** (Bulletins vides)
- **Leere Stimmen** (Votes vides)
- **Listen-Nr** (Numéro de liste)
- **Partei-ID** (Identifiant de parti)
- **Parteibezeichnung** (Description de parti)
- **HLV-Nr**
- **ULV-Nr**
- **Anzahl Sitze Liste** (Liste du nombre de places)
- **Kandidatenstimmen unveränderte Wahlzettel** (Bulletin non modifié des votes de candidats, faisant partie du vote de liste)
- **Zusatzstimmen unveränderte Wahlzettel** (Bulletin non modifié des votes supplémentaires, faisant partie du vote de liste)
- **Kandidatenstimmen veränderte Wahlzettel** (Bulletin modifié des votes de candidats, faisant partie du vote de liste)
- **Zusatzstimmen veränderte Wahlzettel** (Bulletin modifié des votes supplémentaires, faisant partie du vote de liste)
- **Kandidaten-Nr** (Numéro de candidat)
- **Gewählt** (Élu)
- **Name** (Nom)
- **Vorname** (Prénom)
- **Stimmen Total aus Wahlzettel** (Total de votes provenant du bulletin)
- **Anzahl Gemeinden** (Nombre de municipalités)

### Résultats temporaires

On juge que l'élection n'est pas comptée si la quantité de municipalités comptées dans « Nombre de municipalités » ne correspond pas au nombre total de municipalités. Les municipalités qui ne sont pas encore comptées ne sont pas incluses dans les données.

### Modèle

[election_sesam_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_sesam_proporz.csv)

## Wabsti Majorz

Le format de fichier nécessite deux diagrammes individuels : l'exportation des données et la liste des candidats élus.

### Exportation des données de colonnes

Dans l'exportation des données, une ligne est présente pour chaque municipalité, les candidats sont disposés en colonnes. Les colonnes suivantes seront évaluées et on devrait au moins avoir celles-ci :

- **AnzMandate** (Nombre de places)
- **BFS** (Numéro BFS de la municipalité.)
- **StimmBer** (Autorisé à voter)
- **StimmAbgegeben** (Votes)
- **StimmLeer** (Votes vides)
- **StimmUngueltig** (Votes non valides)
- **StimmGueltig** (Votes valides)

Ainsi que pour chaque candidat:

- **KandID_`x`**
- **KandName_`x`**
- **KandVorname_`x`**
- **Stimmen_`x`**

De plus, les votes vides et non valides ainsi que les candidats seront saisis par les noms de candidats suivants :

- **KandName_`x` = 'Leere Zeilen'** (Bulletins vides)
- **KandName_`x` = 'Ungültige Stimmen'** (Bulletins non valides)

### Résultats des candidats de colonnes

Parce que ce format de fichier n'offre aucune information concernant les candidats élus, ceux-ci doivent être inclus dans une deuxième colonne. Chaque ligne est composée d'un candidat élu avec les colonnes suivantes :

- **ID** : Identifiant du candidat (`KandID_x`).
- **Name** : Le nom de famille du candidat.
- **Vorname** : Le prénom du candidat.

### Résultats temporaires

Le format de fichier ne contient aucune information claire sur la situation du comptage complet de l'élection globale. Cette information sera fournie directement dans un formulaire destiné au téléchargement des données.

Le format de fichier ne contient également aucune information sur l'état du comptage complet d'une municipalité individuelle. Ainsi, tant que l'élection entière n'est pas terminée, aucune notification de progrès ne sera affichée pour Wabsti. Si des municipalités manquent complètement dans les résultats, on les considèrera comme pas encore comptées.

### Modèles

[election_wabsti_majorz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_majorz_results.csv)

[election_wabsti_majorz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_majorz_candidates.csv)

## Wabsti Proporz

Le format de fichier nécessite quatre diagrammes individuels : l'exportation des données pour les résultats, l'exportation des données pour les statistiques, les connexions de liste et les candidats élus de liste.

### Exportation des données de résultats pour les colonnes

Une ligne est présente par candidat et municipalité dans l'exportation des données. Les colonnes suivantes seront évaluées et devraient exister :

- **Einheit_BFS** (Numéro BFS de la municipalité.)
- **Kand_Nachname** (Nom de famille du candidat)
- **Kand_Vorname** (Prénom du candidat)
- **Liste_KandID** (Identifiant du candidat)
- **Liste_ID** (Identifiant de la liste de candidats)
- **Liste_Code** (Nom de la liste de candidats)
- **Kand_StimmenTotal** (Nombre de votes de candidats dans la municipalité)
- **Liste_ParteistimmenTotal** (Nombre total de votes de liste.)

### Exportation des données de statistiques pour les colonnes

Le fichier avec les statistiques des municipalités individuelles devrait contenir les colonnes suivantes :

- **Einheit_BFS** (Numéro BFS de la municipalité.)
- **StimBerTotal** (Autorisé à voter)
- **WZEingegangen** (Bulletins)
- **WZLeer** (Bulletins vides)
- **WZUngueltig** (Bulletins non valides)
- **StmWZVeraendertLeerAmtlLeer**

### Connexions de liste des colonnes

Le fichier avec les connexions de liste devrait contenir les colonnes suivantes :

- **Liste** (Liste)
- **LV**
- **LUV**

### Résultats de candidats des colonnes

Da das Datenformat keine Informationen über die gewählten Kandidaten liefert, müssen diese in einer zweiten Tabelle mitgeliefert werden. Jede Zeile enthält dabei eine gewählten Kandidaten mit den folgenden Spalten:

- **ID**: L'identifiant du candidat (`Liste_KandID`).
- **Name**: Le nom de famille du candidat.
- **Vorname**: Le prénom du candidat.

### Résultats temporaires

Le format de fichier ne contient aucune information claire sur la situation du comptage complet de l'élection globale. Cette information sera fournie directement dans un formulaire destiné au téléchargement des données.

Le format de fichier ne contient également aucune information sur l'état du comptage complet d'une municipalité individuelle. Ainsi, tant que l'élection entière n'est pas terminée, aucune notification de progrès ne sera affichée pour Wabsti. Si des municipalités manquent complètement dans les résultats, on les considèrera comme pas encore comptées.

### Modèles

[election_wabsti_proporz_results.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_results.csv)

[election_wabsti_proporz_statistics.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_statistics.csv)

[election_wabsti_proporz_list_connections.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_list_connections.csv)

[election_wabsti_proporz_candidates.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_wabsti_proporz_candidates.csv)


## OneGov

Le format, qui sera utilisé par l'application web pour l'exportation, se compose d'un seul fichier par élection. Une ligne est présente pour chaque municipalité et candidat.

### Colonnes

Les colonnes suivantes seront évaluées et devraient exister :

- **election_absolute_majority**: Majorité absolue de l'élection, seulement si c'est une élection Majorz.
- **election_counted_entities**: Nombre de municipalités comptées. Si `election_counted_entities = election_total_entities`, on considère alors que l'élection est entièrement comptée.
- **election_total_entities**: Nombre total de municipalités. Si aucune information précise à propos de la situation de l'élection n'est possible (parce que l'élection a été importée par Wabsti), alors cette valeur est `0`.
- **entity_id**: Numéro BFS de la municipalité..
- **entity_elegible_voters**: Nombre de personnes autorisées à voter dans la municipalité.
- **entity_received_ballots**: Nombre de bulletins soumis dans la municipalité.
- **entity_blank_ballots**: Nombre de bulletins vides dans la municipalité.
- **entity_invalid_ballots**: Nombre de bulletins non valides dans la municipalité.
- **entity_blank_votes**: Nombre de votes vides dans la municipalité.
- **entity_invalid_votes**: Nombre de votes non valides dans la municipalité. Zéro si c'est une élection Proporz.
- **list_name**: Nom de la liste de candidats. Uniquement avec les élections Proporz.
- **list_id**: Identifiant de la liste de candidats. Uniquement avec les élections Proporz.
- **list_number_of_mandates**: Nombre total de mandats de la liste. Uniquement avec les élections Proporz.
- **list_votes**: Nombre total de votes de liste. Uniquement avec les élections Proporz.
- **list_connection**: Identifiant de la connexion de liste. Uniquement avec les élections Proporz.
- **list_connection_parent**: Identifiant de la connexion de liste au niveau supérieur. Uniquement avec les élections Proporz et si c'est une connexion de sous-liste.
- **candidate_family_name**: Nom de famille du candidat.
- **candidate_first_name**: Prénom du candidat.
- **candidate_elected**: Vrai, si le candidat a été élu.
- **candidate_votes**: Nombre de votes de candidats dans la municipalité.

### Résultats temporaires

On considère que l'élection n'est pas entièrement comptée, si « election_counted_entities » et « election_total_entities » ne correspondent pas. Si « election_total_entities = 0 », aucune information claire n'est alors possible à propos de la situation de l'élection (parce que l'élection a été importée par Wabsti).

Les municipalités pas encore entièrement comptées ne sont pas incluses dans les fichiers.


### Modèle

[election_onegov_majorz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_onegov_majorz.csv)

[election_onegov_proporz.csv](https://raw.githubusercontent.com/OneGov/onegov.election_day/master/docs/election_onegov_proporz.csv)
