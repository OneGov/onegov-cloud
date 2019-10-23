WITH

list_results AS (
    SELECT
    l.election_id,
    c.connection_id,
    pc.connection_id as parent_connection_id,
    CASE
        WHEN pc.connection_id IS NULL
            THEN c.connection_id
            ELSE pc.connection_id
    END as conn,
    CASE
        WHEN c.parent_id IS NULL
            THEN NULL
            ELSE c.connection_id
    END as subconn,
    l.name as list_name,
    SUM(lr.votes) AS list_votes
    FROM lists l
    JOIN list_results lr ON l.id = lr.list_id
    RIGHT JOIN list_connections c ON l.connection_id = c.id
    LEFT JOIN list_connections pc ON c.parent_id = pc.id
    GROUP BY
             l.id,
             l.name,
             l.connection_id,
             c.connection_id,
             parent_connection_id,
             subconn
),

result as (
    SELECT
        lr.election_id,
        lr.connection_id,
        lr.list_name,
        lr.conn,
        lr.subconn,
        lr.list_votes,
        SUM(lr.list_votes) OVER (PARTITION BY lr.election_id, lr.conn, lr.subconn) as subconn_votes,
        SUM(lr.list_votes) OVER (PARTITION BY lr.election_id, lr.conn) as conn_votes,
        SUM(lr.list_votes) OVER(PARTITION BY lr.election_id) AS total_votes
    FROM list_results lr
)

-- The resulting query
SELECT
       v.election_id,       -- Text
       v.connection_id,     -- Text
       v.list_name,         -- Text
       v.conn,              -- Text
       v.subconn,           -- Text
       v.list_votes,        -- Numeric
       v.subconn_votes,     -- Numeric
       v.conn_votes,    -- Numeric
       v.total_votes        -- Numeric
FROM result v
ORDER BY v.conn,
         v.subconn,
         v.subconn_votes DESC,
         v.list_votes DESC


