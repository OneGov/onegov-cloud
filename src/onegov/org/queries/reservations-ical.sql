SELECT
    token,                                -- UUID
    resources.title as resource,          -- UUID
    tickets.number as description,        -- Text
    start,                                -- UTCDateTime
    "end",                                -- UTCDateTime
    tickets.id as ticket_id,              -- UUID
    tickets.handler_code as handler_code, -- Text
    email                                 -- Text

FROM
    reservations

JOIN resources
ON reservations.resource = resources.id

LEFT JOIN tickets
ON reservations.token = tickets.handler_id::uuid

WHERE
    "status" = 'approved'
    AND (("data"::jsonb)->>'accepted')::boolean = TRUE

ORDER BY start
