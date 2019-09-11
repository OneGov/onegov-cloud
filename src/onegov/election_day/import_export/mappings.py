
INTERNAL_COMMON_ELECTION_HEADERS = [
    'election_status',
    'entity_id',
    'entity_counted',
    'entity_eligible_voters',
    'entity_received_ballots',
    'entity_blank_ballots',
    'entity_invalid_ballots',
    'entity_blank_votes',
    'entity_invalid_votes',
    'candidate_family_name',
    'candidate_first_name',
    'candidate_id',
    'candidate_elected',
    'candidate_votes',
    'candidate_party',
]

INTERNAL_PROPORZ_HEADERS = [
    'list_name',
    'list_id',
    'list_number_of_mandates',
    'list_votes',
    'list_connection',
    'list_connection_parent',
] + INTERNAL_COMMON_ELECTION_HEADERS

INTERNAL_MAJORZ_HEADERS = [
    'election_absolute_majority',
] + INTERNAL_COMMON_ELECTION_HEADERS

ELECTION_PARTY_HEADERS = [
    'year',
    'total_votes',
    'name',
    'id',
    'color',
    'mandates',
    'votes',
]

WABSTI_MAJORZ_HEADERS = [
    'anzmandate',
    # 'absolutesmehr' optional
    'bfs',
    'stimmber',
    # 'stimmabgegeben' or 'wzabgegeben'
    # 'wzleer' or 'stimmleer'
    # 'wzungueltig' or 'stimmungueltig'
]

WABSTI_MAJORZ_HEADERS_CANDIDATES = [
    'kandid',
]

WABSTI_PROPORZ_HEADERS = [
    'einheit_bfs',
    'liste_kandid',
    'kand_nachname',
    'kand_vorname',
    'liste_id',
    'liste_code',
    'kand_stimmentotal',
    'liste_parteistimmentotal',
]

WABSTI_PROPORZ_HEADERS_CONNECTIONS = [
    'liste',
    'lv',
    'luv',
]

WABSTI_PROPORZ_HEADERS_CANDIDATES = [
    'liste_kandid'
]

WABSTI_PROPORZ_HEADERS_STATS = [
    'einheit_bfs',
    'einheit_name',
    'stimbertotal',
    'wzeingegangen',
    'wzleer',
    'wzungueltig',
    'stmwzveraendertleeramtlleer',
]

WABSTIC_MAJORZ_HEADERS_WM_WAHL = (
    'sortgeschaeft',  # provides the link to the election
    'absolutesmehr',  # absolute majority
    'ausmittlungsstand',  # complete
)
WABSTIC_MAJORZ_HEADERS_WMSTATIC_GEMEINDEN = (
    'sortwahlkreis',  # provides the link to the election
    'sortgeschaeft',  # provides the link to the election
    'bfsnrgemeinde',  # BFS
    'stimmberechtigte',  # eligible votes
)
WABSTIC_MAJORZ_HEADERS_WM_GEMEINDEN = (
    'bfsnrgemeinde',  # BFS
    'stimmberechtigte',  # eligible votes
    'sperrung',  # counted
    'stmabgegeben',  # received ballots
    'stmleer',  # blank ballots
    'stmungueltig',  # invalid ballots
    'stimmenleer',  # blank votes
    'stimmenungueltig',  # invalid votes
)
WABSTIC_MAJORZ_HEADERS_WM_KANDIDATEN = (
    'sortgeschaeft',  # provides the link to the election
    'knr',  # candidate id
    'nachname',  # familiy name
    'vorname',  # first name
    'gewaehlt',  # elected
    'partei',  #
)
WABSTIC_MAJORZ_HEADERS_WM_KANDIDATENGDE = (
    'sortgeschaeft',  # provides the link to the election
    'bfsnrgemeinde',  # BFS
    'knr',  # candidate id
    'stimmen',  # votes
)

WABSTIC_PROPORZ_HEADERS_WP_WAHL = (
    'sortgeschaeft',  # provides the link to the election
    'ausmittlungsstand',  # complete
)
WABSTIC_PROPORZ_HEADERS_WPSTATIC_GEMEINDEN = (
    'sortwahlkreis',  # provides the link to the election
    'sortgeschaeft',  # provides the link to the election
    'bfsnrgemeinde',  # BFS
    'stimmberechtigte',  # eligible votes
)
WABSTIC_PROPORZ_HEADERS_WP_GEMEINDEN = (
    'bfsnrgemeinde',  # BFS
    'stimmberechtigte',  # eligible votes
    'sperrung',  # counted
    'stmabgegeben',  # received ballots
    'stmleer',  # blank ballots
    'stmungueltig',  # invalid ballots
    'anzwzamtleer',  # blank ballots
)
WABSTIC_PROPORZ_HEADERS_WP_LISTEN = (
    'sortgeschaeft',  # provides the link to the election
    'listnr',
    'listcode',
    'sitze',
    'listverb',
    'listuntverb',
)
WABSTIC_PROPORZ_HEADERS_WP_LISTENGDE = (
    'bfsnrgemeinde',  # BFS
    'listnr',
    'stimmentotal',
)
WABSTIC_PROPORZ_HEADERS_WPSTATIC_KANDIDATEN = (
    'sortgeschaeft',  # provides the link to the election
    'knr',  # candidate id
    'nachname',  # familiy name
    'vorname',  # first name
)
WABSTIC_PROPORZ_HEADERS_WP_KANDIDATEN = (
    'sortgeschaeft',  # provides the link to the election
    'knr',  # candidate id
    'gewaehlt',  # elected
)
WABSTIC_PROPORZ_HEADERS_WP_KANDIDATENGDE = (
    'bfsnrgemeinde',  # BFS
    'knr',  # candidate id
    'stimmen',  # votes
)

# VOTES

DEFAULT_VOTE_HEADER = [
    'id',
    'ja stimmen',
    'nein stimmen',
    'Stimmberechtigte',
    'leere stimmzettel',
    'ungültige stimmzettel'
]

INTERNAL_VOTE_HEADERS = [
    'status',
    'type',
    'entity_id',
    'counted',
    'yeas',
    'nays',
    'invalid',
    'empty',
    'eligible_voters',
]

WABSTI_VOTE_HEADERS = (
    'vorlage-nr.',
    'bfs-nr.',
    'stimmberechtigte',
    'leere sz',
    'ungultige sz',
    'ja',
    'nein',
    'gegenvja',
    'gegenvnein',
    'stichfrja',
    'stichfrnein',
    'stimmbet',
)

WABSTIC_VOTE_HEADERS_SG_GESCHAEFTE = (
    'art',  # domain
    'sortwahlkreis',
    'sortgeschaeft',  # vote number
    'ausmittlungsstand'
)

WABSTIC_VOTE_HEADERS_SG_GEMEINDEN = (
    'art',  # domain
    'sortwahlkreis',
    'sortgeschaeft',  # vote number
    'bfsnrgemeinde',  # BFS
    'sperrung',  # counted
    'stimmberechtigte',   # eligible votes
    'stmungueltig',  # invalid
    'stmleer',  # empty (proposal if simple)
    'stmhgja',  # yeas (proposal)
    'stmhgnein',  # nays (proposal)
    'stmhgohneaw',  # empty (proposal if complex)
    'stmn1ja',  # yeas (counter-proposal)
    'stmn1nein',  # nays (counter-proposal)
    'stmn1ohneaw',  # empty (counter-proposal)
    'stmn2ja',  # yeas (tie-breaker)
    'stmn2nein',  # nays (tie-breaker)
    'stmn2ohneaw',  # empty (tie-breaker)
)

WABSTIM_VOTE_HEADERS = (
    'freigegeben',
    'stileer',
    'stiungueltig',
    'stijahg',
    'stineinhg',
    'stiohneawhg',
    'stijan1',
    'stineinn1',
    'stiohneawN1',
    'stijan2',
    'stineinn2',
    'stiohneawN2',
    'stimmberechtigte',
    'bfs',
)