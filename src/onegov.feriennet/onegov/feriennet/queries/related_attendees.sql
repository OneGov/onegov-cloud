/*
    Attendees related to a set of occasions
*/
SELECT
    occasion_id,                  -- UUID
    attendee_count,               -- Integer
    parent,                       -- Text
    parent_username,              -- Text
    COUNT(child) AS children,     -- Integer
    phone,                        -- Text
    place,                        -- Text
    email,                        -- Text
    booking_state                 -- Text
FROM (
    SELECT
        users.username AS parent_username,
        COALESCE(users.realname, users.username) AS parent,
        attendees.name AS child,
        users.data->>'phone' AS phone,
        users.data->>'place' AS place,
        CASE users.data->>'email'
            WHEN '' THEN users.username
            ELSE users.data->>'email'
        END as email,
        occasion_id,
        bookings.state AS booking_state,
        COUNT(*) OVER (PARTITION BY occasion_id) AS attendee_count
    FROM bookings
        LEFT JOIN attendees ON attendee_id = attendees.id
        LEFT JOIN users ON bookings.username = users.username
) AS attendee_list
GROUP BY occasion_id, attendee_count, parent, parent_username, phone, place, email, booking_state
ORDER BY occasion_id, lower(unaccent(parent))
