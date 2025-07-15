SELECT
    reservations.id as id,                -- Integer
    token,                                -- UUID
    resource,                             -- UUID
    tickets.subtitle as title,            -- Text
    tickets.number as description,        -- Text
    "start",                              -- UTCDateTime
    "end",                                -- UTCDateTime
    tickets.id as ticket_id,              -- UUID
    tickets.handler_code as handler_code  -- Text

FROM
    reservations

LEFT JOIN tickets
ON reservations.token = tickets.handler_id::uuid

WHERE
    "status" = 'approved'
    AND ("data"->'accepted')::boolean IS TRUE

ORDER BY "start"
