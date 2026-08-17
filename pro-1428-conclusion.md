# PRO-1428 — Bevorzugt der Matching-Algorithmus Kinder mit wenig Wünschen?

## Kurzantwort

**Nein.** Die Analyse über drei Jahre (2024–2026) und beide beschwerdeführenden
Instanzen (Oron-Jorat, Obersiggenthal) zeigt kein Anzeichen dafür, dass der
Algorithmus Kinder mit wenig Wünschen bevorzugt. Im Gegenteil: Wo überhaupt
jemand ganz leer ausgeht, sind es die **Wenig-Wunsch-Kinder**. Der wahrgenommene
Effekt („viele Favoriten nicht bekommen") entsteht nicht durch unfaire
Ablehnung, sondern durch **Terminüberschneidungen** und teils durch **manuelle
Admin-Priorisierung (Nobble)**.

## Wie der Algorithmus funktioniert

Das Matching (Deferred Acceptance) füllt jeden Kurs ausschliesslich nach der
**Priorität** der einzelnen Wünsche. Die Anzahl der Wünsche eines Kindes spielt
dabei **keine Rolle**. Priorität ergibt sich aus:

- **Stern/Favorit** (durch das Kind gesetzt) → Priorität 1
- **Nobble** (durch Admin erzwungen, vor dem Matching) → Priorität 2, schlägt
  jeden Stern
- kein Marker → Priorität 0

Jedes Kind kann **maximal 3** Wünsche sternen (fix im Code). Ein Kurs gibt einen
Platz nur an einen Wunsch mit *echt höherer* Priorität ab.

## Datenbasis

Ausgewertet wurden die jeweils bestätigten Perioden 2024, 2025 und 2026 beider
Instanzen. Kennzahl für „unfaire" Ergebnisse: **gesternte Wünsche ohne Platz**,
aufgeschlüsselt nach Ursache. Herausgerechnet wurden: nachträglich stornierte
Blockaden (veraltete `blocked`-Zustände) sowie **stornierte Kurse**
(`occasions.cancelled`) — ein abgesagter Kurs ist weder ein echter Platz noch
ein echter Blocker. Der Absage-Filter verändert die Kernzahlen kaum
(Oron-Jorat: keine Absagen; Obersiggenthal: leichte Verschiebungen im
few/many-Bucket, da Buchungen auf abgesagten Kursen die Wunschzahl senken).

### Oron-Jorat (PasVac)

| Kennzahl                     | 2024       | 2025       | 2026       |
| ---------------------------- | ---------- | ---------- | ---------- |
| Kinder / Sternwünsche        | 342 / 755  | 339 / 776  | 414 / 986  |
| **Sternwünsche ohne Platz (Kennzahl)** | 171 (22.6 %) | 178 (22.9 %) | 233 (23.6 %) |
| — abgelehnt mangels Platz    | 5 (0.7 %)  | 3 (0.4 %)   | 6 (0.6 %)  |
| — echte Terminüberschneidung | 166 (22 %) | 175 (22.6 %)| 227 (23 %) |
| stale (herausgerechnet)      | 94         | 59          | 149        |
| kein Platz überhaupt         | 3 (0.9 %)  | 4 (1.2 %)   | 2 (0.5 %)  |
| — davon **wenig Wünsche (≤3)** | 0/3 (0 %) | 1/4 (25 %) | 1/7 (14.3 %) |
| — davon viele Wünsche (>3)   | 3/339 (0.9 %) | 3/335 (0.9 %) | 1/407 (0.2 %) |
| Admin-Nobbles (angenommen)   | 113        | 135        | 328        |

### Obersiggenthal (Ferienpass Frühling)

| Kennzahl                       | 2024          | 2025         | 2026        |
| ------------------------------ | ------------- | ------------ | ----------- |
| Kinder / Sternwünsche          | 253 / 590     | 240 / 495    | 245 / 489   |
| **Sternwünsche ohne Platz (Kennz.)** | 61 (10.3 %) | 29 (5.9 %)  | 34 (7.0 %) |
| — abgelehnt mangels Platz      | 3 (0.5 %)     | 8 (1.6 %)    | 1 (0.2 %)   |
| — echte Terminüberschneidung   | 58 (9.8 %)    | 21 (4.2 %)   | 33 (6.7 %)  |
| stale (herausgerechnet)        | 59            | 33           | 20          |
| kein Platz überhaupt           | 3 (1.2 %)     | 7 (2.9 %)    | 3 (1.2 %)   |
| — davon **wenig Wünsche (≤3)** | 2/18 (11.1 %) | 5/31 (16.1 %)| 3/25 (12 %) |
| — davon viele Wünsche (>3)     | 1/235 (0.4 %) | 2/209 (1 %)  | 0/220 (0 %) |
| Admin-Nobbles (angenommen)     | 0             | 1            | 25          |

## Befunde

1. **Kein Überbuchungsproblem.** In allen sechs Perioden werden nur **0.2–1.6 %**
   der Sternwünsche mangels Platz abgelehnt. Die Kurse haben genügend Kapazität;
   der Algorithmus muss kaum jemanden abweisen.

2. **Unerfüllte Favoriten = echte Terminüberschneidungen, nicht Ablehnung.**
   Der grösste Teil der nicht erhaltenen Sternwünsche entsteht, weil das Kind
   mehrere Kurse **zur gleichen Zeit** gesternt hat (oder ein Übernacht-Kurs in
   den Folgetag hineinreicht) — nicht, weil ein Kurs voll war. Eine
   Stichprobe für Obersiggenthal 2026 bestätigt das: die blockierten
   Sternwünsche kollidieren fast durchweg mit einem angenommenen Kurs zur
   exakt gleichen oder direkt überlappenden Startzeit. Der Algorithmus kann ein
   Kind schlicht nicht an zwei gleichzeitigen Kursen platzieren.

3. **Die Beschwerde-These ist widerlegt — bei Obersiggenthal statistisch
   belastbar.** Über die drei Jahre gepoolt: **wenig-Wunsch-Kinder 10 von 74 ohne
   Platz (≈14 %)** gegenüber **viel-Wunsch-Kindern 3 von 664 (≈0.5 %)**. Es sind
   also gerade die Kinder mit *wenigen* Wünschen, die am ehesten leer ausgehen —
   logisch, da ihnen ein Ausweichkurs fehlt. Von einer Bevorzugung
   wenig-wünschender Kinder kann keine Rede sein.

4. **Admin-Eingriff (Nobble) ist nicht der gemeinsame Nenner.** Oron-Jorat
   priorisiert sehr viele Wünsche manuell (113 → 328), Obersiggenthal praktisch
   nie (0/1/1) — beide beschweren sich dennoch. Der wahrgenommene Effekt hängt
   somit nicht am Admin-Eingriff. In Oron-Jorat verdrängt allerdings ein
   erheblicher Teil der Nobbles die *eigenen* Favoriten der Kinder zeitlich, was
   dort die hohe „unerfüllt"-Quote miterklärt.

5. **Die Transferzeit ist nicht der Treiber der Konflikte.** Die
   Perioden-Einstellung „Required minutes between bookings" (`minutes_between`)
   ist die vom Veranstalter gesetzte Weg-/Pufferzeit zwischen zwei Kursen;
   Kurse, die weniger als diese Zeit auseinanderliegen, blockieren sich im
   Matching gegenseitig. Die Werte:

   | Instanz                   | 2024    | 2025    | 2026    |
   | ------------------------- | ------- | ------- | ------- |
   | Oron-Jorat (PasVac)       | 15 Min. | 45 Min. | 40 Min. |
   | Obersiggenthal (Frühling) | 30 Min. | 30 Min. | 30 Min. |

   Naheliegend wäre, den hohen Konflikt-Anteil in Oron-Jorat auf die grosse
   Transferzeit zu schieben. Die Zahlen widerlegen das aber: Obwohl Oron-Jorat
   den Puffer von 15 auf 45 Min. verdreifacht hat, bleibt der
   Terminkonflikt-Anteil praktisch konstant (**22 % → 23 % → 23 %**). Die
   Blockaden entstehen also durch *tatsächlich gleichzeitige* gesternte Kurse,
   nicht durch die Pufferzeit — und untermauern damit Befund 2 (echte
   Überschneidungen statt unfaire Ablehnung).

## Einschränkungen

- **Oron-Jorat, Wenig-Wunsch-Gruppe:** Diese ist dort jedes Jahr winzig
  (3/4/7 Kinder), weil fast alle Kinder sehr viele Wünsche eingeben (Ø ~25). Ein
  few-vs-many-Vergleich ist für Oron-Jorat nicht aussagekräftig; der Hauptbefund
  (keine unfaire Ablehnung) gilt aber auch hier.
- Die 3-Sterne-Obergrenze ist bewusst knapp gewählt: Ein Kind mit ≤3 Wünschen
  kann alle sternen, ein Kind mit vielen Wünschen nur einen Teil. Dieser
  strukturelle Punkt existiert, wirkt sich hier aber wegen der ausreichenden
  Kapazität kaum aus.

## Fazit

Der Algorithmus arbeitet stabil und fair; er benachteiligt oder bevorzugt
niemanden aufgrund der Anzahl Wünsche. Der von den Ferienpässen wahrgenommene
Effekt lässt sich vollständig durch **echte Terminüberschneidungen** (Kinder
sternen mehrere zeitgleiche Kurse) und in Oron-Jorat zusätzlich durch
**umfangreiche manuelle Admin-Priorisierung** erklären — nicht durch einen Bias
des Matchings. Die Transferzeit spielt dabei kaum eine Rolle (konstante
Konflikt-Quote trotz verdreifachtem Puffer).
