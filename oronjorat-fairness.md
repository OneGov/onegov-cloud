# Oron-Jorat — match-fairness (PasVac 2024–2026)

Rohausgabe des `match-fairness`-CLI (mit Absage-Filter: stornierte Buchungen
und stornierte Kurse ausgeschlossen; veraltete Blockaden getrennt ausgewiesen).

## PasVac 2024

```
children: 342, bookings: 7950

overall:
  starred wishes unfulfilled (excl. stale): 171/755 (22.6%)
    - rejected (no spot):        5 (0.7%)
    - overlapping (real conflict): 166 (22.0%)
  stale blocked (blocker cancelled, ignored): 94
  children with no place at all: 3/342 (0.9%)
  admin-prioritized (nobbled, set before matching): 114 wishes, of which accepted 113 (6.8% of all places)

by wishlist size (star cap = 3):
  few wishes (<= 3): 3 children, starred unfulfilled 0/1 (rejected 0, overlapping 0; stale 0), no place 0/3 (0.0%)
  many wishes (> 3): 339 children, starred unfulfilled 171/754 (rejected 5, overlapping 166; stale 94), no place 3/339 (0.9%)
```

## PasVac 2025

```
children: 339, bookings: 8731

overall:
  starred wishes unfulfilled (excl. stale): 178/776 (22.9%)
    - rejected (no spot):        3 (0.4%)
    - overlapping (real conflict): 175 (22.6%)
  stale blocked (blocker cancelled, ignored): 59
  children with no place at all: 4/339 (1.2%)
  admin-prioritized (nobbled, set before matching): 146 wishes, of which accepted 135 (7.1% of all places)

by wishlist size (star cap = 3):
  few wishes (<= 3): 4 children, starred unfulfilled 0/0 (rejected 0, overlapping 0; stale 0), no place 1/4 (25.0%)
  many wishes (> 3): 335 children, starred unfulfilled 178/776 (rejected 3, overlapping 175; stale 59), no place 3/335 (0.9%)
```

## PasVac 2026

```
children: 414, bookings: 10274

overall:
  starred wishes unfulfilled (excl. stale): 233/986 (23.6%)
    - rejected (no spot):        6 (0.6%)
    - overlapping (real conflict): 227 (23.0%)
  stale blocked (blocker cancelled, ignored): 149
  children with no place at all: 2/414 (0.5%)
  admin-prioritized (nobbled, set before matching): 331 wishes, of which accepted 328 (16.6% of all places)

by wishlist size (star cap = 3):
  few wishes (<= 3): 7 children, starred unfulfilled 1/2 (rejected 1, overlapping 0; stale 0), no place 1/7 (14.3%)
  many wishes (> 3): 407 children, starred unfulfilled 232/984 (rejected 5, overlapping 227; stale 149), no place 1/407 (0.2%)
```

## Beobachtungen

- **Kein Überbuchungsproblem:** rejected (kein Platz) konstant 0.4–0.7 %.
- Unerfüllte Favoriten sind fast ausschliesslich **echte Terminkonflikte**
  (~22–23 %), stabil über drei Jahre.
- Fast alle Kinder bekommen einen Platz (kein Platz: 0.5–1.2 %).
- **Sehr viele Wünsche pro Kind** (Ø ~22–25) → die few-Gruppe (≤3 Wünsche) ist
  mit 3–7 Kindern winzig und nicht aussagekräftig.
- Starker Admin-Eingriff (nobbled accepted 113 → 135 → 328).
