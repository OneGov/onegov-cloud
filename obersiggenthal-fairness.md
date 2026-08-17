# Obersiggenthal — match-fairness (Ferienpass Frühling 2024–2026)

Rohausgabe des `match-fairness`-CLI (mit Absage-Filter: stornierte Buchungen
und stornierte Kurse ausgeschlossen; veraltete Blockaden getrennt ausgewiesen).

## Ferienpass Frühling 2024

```
children: 253, bookings: 1853

overall:
  starred wishes unfulfilled (excl. stale): 61/590 (10.3%)
    - rejected (no spot):        3 (0.5%)
    - overlapping (real conflict): 58 (9.8%)
  stale blocked (blocker cancelled, ignored): 59
  children with no place at all: 3/253 (1.2%)
  admin-prioritized (nobbled, set before matching): 0 wishes, of which accepted 0 (0.0% of all places)

by wishlist size (star cap = 3):
  few wishes (<= 3): 18 children, starred unfulfilled 0/12 (rejected 0, overlapping 0; stale 1), no place 2/18 (11.1%)
  many wishes (> 3): 235 children, starred unfulfilled 61/578 (rejected 3, overlapping 58; stale 58), no place 1/235 (0.4%)
```

## Ferienpass Frühling 2025

```
children: 240, bookings: 1619

overall:
  starred wishes unfulfilled (excl. stale): 29/495 (5.9%)
    - rejected (no spot):        8 (1.6%)
    - overlapping (real conflict): 21 (4.2%)
  stale blocked (blocker cancelled, ignored): 33
  children with no place at all: 7/240 (2.9%)
  admin-prioritized (nobbled, set before matching): 1 wishes, of which accepted 1 (0.1% of all places)

by wishlist size (star cap = 3):
  few wishes (<= 3): 31 children, starred unfulfilled 3/19 (rejected 3, overlapping 0; stale 1), no place 5/31 (16.1%)
  many wishes (> 3): 209 children, starred unfulfilled 26/476 (rejected 5, overlapping 21; stale 32), no place 2/209 (1.0%)
```

## Ferienpass Frühling 2026

```
children: 245, bookings: 1723

overall:
  starred wishes unfulfilled (excl. stale): 34/489 (7.0%)
    - rejected (no spot):        1 (0.2%)
    - overlapping (real conflict): 33 (6.7%)
  stale blocked (blocker cancelled, ignored): 20
  children with no place at all: 3/245 (1.2%)
  admin-prioritized (nobbled, set before matching): 25 wishes, of which accepted 25 (2.3% of all places)

by wishlist size (star cap = 3):
  few wishes (<= 3): 25 children, starred unfulfilled 1/4 (rejected 1, overlapping 0; stale 0), no place 3/25 (12.0%)
  many wishes (> 3): 220 children, starred unfulfilled 33/485 (rejected 0, overlapping 33; stale 20), no place 0/220 (0.0%)
```

## Beobachtungen

- **Kein Überbuchungsproblem:** rejected (kein Platz) konstant 0.2–1.6 %.
- Unerfüllte Favoriten sind fast ausschliesslich **echte Terminkonflikte**
  (4–10 %).
- **Klares Muster über drei Jahre:** wer ganz ohne Platz bleibt, sind eher die
  **Wenig-Wunsch-Kinder** — few (≤3): 11.1 % / 16.1 % / 12.0 % gegenüber
  many (>3): 0.4 % / 1.0 % / 0.0 %.
- Praktisch **kein Admin-Eingriff** (nobbled accepted 0 / 1 / 25) — im Gegensatz
  zu Oron-Jorat, das trotzdem dieselbe Beschwerde hat.
