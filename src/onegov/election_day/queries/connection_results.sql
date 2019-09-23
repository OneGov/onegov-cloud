SELECT
    lc.id,
    lc.connection_id,
    lc.election_id
FROM list_connections lc
WHERE lc.election_id = 'nationalratswahlen-2019'
ORDER BY lc.connection_id
