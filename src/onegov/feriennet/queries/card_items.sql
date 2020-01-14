SELECT
    occasion_needs.id AS need_id,       -- UUID
    occasion_needs.name AS need_name,   -- Text
    occasion_dates.start AS "start",    -- UTCDateTime
    occasion_dates.end AS "end",        -- UTCDateTime
    activities.title AS activity_title, -- Text
    occasions.id AS occasion_id         -- UUID
FROM
    occasion_needs
    JOIN occasions ON occasion_needs.occasion_id = occasions.id
    JOIN occasion_dates ON occasion_dates.occasion_id = occasions.id
    JOIN activities ON occasions.activity_id = activities.id
ORDER BY
    activities.title,
    occasion_needs.occasion_id,
    occasion_dates.start,
    occasion_needs.name,
    occasion_needs.id
