------------------------------------------------------------------------------------
-- Queries for integrity checks (i.e., verifying synthetic data is logically valid)
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- INTEGRITY (CHECKING IMPOSSIBLE PATTERNS)
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- STREAMS BEFORE SIGNUP?
------------------------------------------------------------------------------------
SELECT COUNT(*) AS streams_before_signup
FROM users
JOIN streams ON streams.user_id = users.id
WHERE users.signup_date > streams.start_datetime;

-- RESULTS:
-- 791 streams exist before the corresponding user's signup date.
-- TO DO: limit signup_date to at most two years from today
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- STREAMS IN THE FUTURE?
------------------------------------------------------------------------------------
SELECT start_datetime AS future_streams
FROM streams
WHERE start_datetime > (SELECT DATE('now', 'localtime'))
ORDER BY start_datetime DESC;

-- RESULTS:
-- Returns 77 streams, all on the current date but
-- some at times later than the current time.
-- Acceptable for now -- not a major issue
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- SONGS PLAYED LONGER THAN DURATION?
------------------------------------------------------------------------------------
SELECT COUNT(*) AS streams_longer_than_song
FROM streams
JOIN songs ON songs.id = streams.song_id
WHERE ms_played > duration_ms;

-- RESULTS:
-- 0 streams that are longer than a song
------------------------------------------------------------------------------------

------------------------------------------------------------------------------------
-- BEHAVIORAL CONSISTENCY
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- SKIP-RATE VALIDATION
------------------------------------------------------------------------------------
-- QUESTION: At what rate are users skipping songs?

SELECT user_id, AVG(skipped) AS skip_rate
FROM streams
GROUP BY user_id
ORDER BY user_id ASC;

-- RESULTS:
-- skip_rates range from 0.032 to 0.54,
-- approximately aligning with user's generated skip_rates
-- (which range from 0.05 to 0.4)
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- TIME PREFERENCE VALIDATION
------------------------------------------------------------------------------------
-- QUESTION: Is user listening activity concentrated at certain times?

SELECT user_id,
       strftime('%H', start_datetime) AS hour,
       COUNT(*) AS stream_count
FROM streams
GROUP BY user_id, hour
ORDER BY user_id, stream_count DESC LIMIT 50;

-- RESULTS:
-- some users concentrated at night, some during daytime,
-- validating day/night listener_type model
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- GENRE PREFERENCE VALIDATION
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- QUESTION: Do users disproportionately listen to certain genres?
------------------------------------------------------------------------------------
SELECT streams.user_id, genres.name, COUNT(*) AS stream_count
FROM streams
JOIN song_genres ON song_genres.song_id = streams.song_id
JOIN genres ON genres.id = song_genres.genre_id
GROUP BY streams.user_id, genres.name
ORDER BY streams.user_id DESC, stream_count DESC;

-- RESULTS:
-- Each user streams between 6–23 distinct genres, but stream counts are
-- concentrated in 1–3 genres per user, reflecting the 1–3 favorite genres
-- assigned during data generation.
------------------------------------------------------------------------------------

------------------------------------------------------------------------------------
-- DISTRIBUTION SANITY CHECKS
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- ENSURE USERS HAVE VARYING GENRE COUNTS
------------------------------------------------------------------------------------
WITH genres_streamed_by_user AS (
SELECT streams.user_id AS user_id,
       COUNT(DISTINCT song_genres.genre_id) AS genres_streamed
FROM streams
JOIN song_genres ON song_genres.song_id = streams.song_id
GROUP BY streams.user_id
)
-- Identifying the most dominant values (number of genres streamed)
SELECT genres_streamed,
       COUNT(*) as frequency,
       CAST(COUNT(*) AS REAL) * 100 /
       (SELECT COUNT(*) FROM genres_streamed_by_user) AS percentage
FROM genres_streamed_by_user
GROUP BY genres_streamed
ORDER BY frequency DESC;

-- RESULTS:
-- genre diversity is broadly distributed across users,
-- with no strong concentration around a single value.
-- Most users stream between 11 and 19 genres,
-- suggesting the 60/40 genre preference model produces
-- both preference clustering and exploration.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- ENSURE USERS HAVE VARYING STREAM COUNTS
------------------------------------------------------------------------------------
WITH streams_per_user AS (
SELECT user_id, COUNT(*) as total_streams
FROM streams
GROUP BY user_id
)
-- Identifying the most dominant values (number of streams per user)
SELECT total_streams,
       COUNT(*) as frequency,
       CAST(COUNT(*) AS REAL) * 100 /
       (SELECT COUNT(*) FROM streams_per_user) AS percentage
FROM streams_per_user
GROUP BY total_streams
ORDER BY frequency DESC;

-- RESULTS:
-- Stream counts are reasonably spread between 25 and 99.
-- No dominant stream-count interval exists,
-- indicating users exhibit varied listening activity levels.
------------------------------------------------------------------------------------
