------------------------------------------------------------------------------------
-- VALIDATION QUERIES (V2)
------------------------------------------------------------------------------------
-- Database updated on June 3, 2026 to increase users, songs, and streams.

-- VERSION 2:
-- * 500 users
-- * 2199 songs
-- * 1041 artists
-- * 1725 albums
-- * 75 genres
-- * 145079 streams
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- STREAMS BEFORE SIGNUP
------------------------------------------------------------------------------------
SELECT COUNT(*)
FROM streams
JOIN users ON streams.user_id = users.id
WHERE start_datetime < signup_date;

-- RESULTS:
-- 10 streams before signup -- all on the same date as signup
-- but at earlier times.

-- FIXED:
-- updated code for generating start_datetimes by using
-- signup_date + timedelta(days=1) as the start of the older streams range
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- INVALID COMPLETION RATE
------------------------------------------------------------------------------------
SELECT COUNT(*)
FROM streams
JOIN songs ON streams.song_id = songs.id
WHERE CAST(ms_played AS REAL) / duration_ms > 1;

-- RESULTS:
-- 0 streams longer than song duration.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- STREAM COUNT DISTRIBUTION BY ACTIVITY LEVEL
------------------------------------------------------------------------------------
SELECT user_id, COUNT(*) AS stream_count
FROM streams
GROUP BY user_id
ORDER BY stream_count DESC;

-- RESULTS:
-- Streams ranging from 50 to 999
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- HOUR DISTRIBUTION
------------------------------------------------------------------------------------
SELECT strftime('%H', start_datetime) AS hour,
       COUNT(*) AS streams
FROM streams
GROUP BY hour
ORDER BY hour;

-- RESULTS:
-- Streams noticeably concentrated between 9am-2pm and 8pm-1am,
-- verifying the day/night bias implemented in stream generation.
------------------------------------------------------------------------------------

