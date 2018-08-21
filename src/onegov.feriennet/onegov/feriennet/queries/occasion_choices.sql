SELECT
    occasions.id AS occasion_id,      -- UUID
    activities.title,                 -- Text
    occasions.cancelled,              -- Boolean
    participants.count,               -- Integer
    occasions.period_id AS period_id, -- UUID
    ARRAY(
        SELECT ARRAY[
            (occasion_dates.start AT TIME ZONE 'UTC') AT TIME ZONE occasion_dates.timezone,
            (occasion_dates.end AT TIME ZONE 'UTC') AT TIME ZONE occasion_dates.timezone
        ] FROM occasion_dates
        WHERE occasion_dates.occasion_id = occasions.id
    ) AS dates                        -- ARRAY(DateTime)

FROM occasions

JOIN activities
  ON occasions.activity_id = activities.id

JOIN LATERAL (
    SELECT COUNT(*) as count
    FROM bookings
    WHERE bookings.occasion_id = occasions.id
) AS participants ON TRUE

ORDER BY
    activities.order,
    occasions.order
