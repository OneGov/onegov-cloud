SELECT
    reservations.id as id,                     -- Integer
    token,                                     -- UUID
    "start",                                   -- UTCDateTime
    "end",                                     -- UTCDateTime
    ("data"->'accepted')::boolean as accepted, -- Boolean
    reservations.timezone as timezone,         -- Text
    resources.title as resource,               -- UUID
    tickets.id as ticket_id,                   -- UUID
    tickets.handler_code as handler_code,      -- Text
    tickets.number as ticket_number,           -- Text
    email,                                     -- Text
    "data"#>>'{kaba,code}' as key_code         -- Text

FROM
    reservations

JOIN resources
ON reservations.resource = resources.id

LEFT JOIN tickets
ON reservations.token = tickets.handler_id::uuid

WHERE
    "status" = 'approved'

ORDER BY "start"
