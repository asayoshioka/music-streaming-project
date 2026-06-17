------------------------------------------------------------------------------------
-- BEHAVIORAL ANALYSIS QUERIES
-- (e.g. top genres, stream counts, hourly listening, skip-rate analysis)
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *********** USER BEHAVIOR ANALYTICS ***********
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** MOST ACTIVE LISTENERS ***
------------------------------------------------------------------------------------
-- QUESTION:
-- What users have the most streams overall?

-- QUERY:
SELECT users.username, users.country, COUNT(*) AS total_streams
FROM users
JOIN streams ON streams.user_id = users.id
GROUP BY users.id
ORDER BY total_streams DESC
LIMIT 20;

-- RESULTS:
-- The top 20 users are spread across various countries,
-- with 30% from the U.S and stream counts ranging from 79-99.

-- INTERPRETATION:
-- U.S.-based users appear somewhat overrepresented among
-- the top listeners, consistent with the seeding bias
-- toward U.S. users.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** TOTAL LISTENING TIME PER USER ***
------------------------------------------------------------------------------------
-- QUESTION:
-- How much time overall do users spend streaming?

-- QUERY:
SELECT users.username,
       SUM(ms_played) / (1000 * 60) AS total_min_streamed
FROM users
JOIN streams ON streams.user_id = users.id
GROUP BY users.id
ORDER BY total_min_streamed DESC;

WITH streaming_min AS (
    SELECT users.username,
       SUM(ms_played) / (1000 * 60) AS total_min_streamed
    FROM users
    JOIN streams ON streams.user_id = users.id
    GROUP BY users.id
    ORDER BY total_min_streamed DESC
)
SELECT AVG(total_min_streamed)
FROM streaming_min;

-- RESULTS:
-- Total minutes streamed per user ranges from 35 to 206,
-- with an average of 97.1 minutes per user.
-- 44% of users have streamed over 100 minutes.

-- INTERPRETATION:
-- Listening time varies substantially across users,
-- with nearly half of users exceeding 100 total minutes streamed.
-- This suggests the synthetic stream generation produces
-- reasonably differentiated listener activity levels.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** AVERAGE COMPLETION RATE PER USER ***
------------------------------------------------------------------------------------
-- QUESTION:
-- Which users tend to finish songs and which skip frequently?

-- QUERY:
SELECT users.username, AVG(CAST(ms_played AS REAL) / duration_ms) AS avg_completion_rate
FROM users
JOIN streams ON streams.user_id = users.id
JOIN songs ON songs.id = streams.song_id
GROUP BY users.id
ORDER BY avg_completion_rate DESC;

-- RESULTS:
-- Average completion rate ranges from 0.33 to 0.64.

-- INTERPRETATION:
-- Completion rates range from roughly one-third
-- to nearly two-thirds of song duration on average.
-- This spread suggests users exhibit meaningfully different
-- listening behaviors, consistent with the assigned skip-rate model.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** FAVORITE GENRES BY ACTUAL BEHAVIOR ***
------------------------------------------------------------------------------------
-- QUESTION:
-- What are each user's favorite genre based on streaming activity?

-- QUERY:
WITH genre_counts AS (
    SELECT users.username,
           genres.name AS genre,
           COUNT(*) AS stream_count,
           ROW_NUMBER() OVER (
                PARTITION BY users.id
                ORDER BY COUNT(*) DESC
           ) AS rn
    FROM streams
    JOIN song_genres ON song_genres.song_id = streams.song_id
    JOIN genres ON genres.id = song_genres.genre_id
    JOIN users ON users.id = streams.user_id
    GROUP BY users.id, genres.id
)
SELECT username, genre, stream_count
FROM genre_counts
WHERE rn = 1
ORDER BY genre ASC;

-- RESULTS:
-- Among all users, there are 38 distinct top genres.
-- Top genres seem to be reasonably varied, with groups of
-- roughly 3-5 people per top genre.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** GENRE DIVERSITY ***
------------------------------------------------------------------------------------
-- QUESTION:
-- How many distinct genres has each user streamed?

-- QUERY:
WITH top_genres_per_user AS (
    SELECT users.username, genres.name, COUNT(*) AS stream_count
    FROM streams
    JOIN song_genres ON song_genres.song_id = streams.song_id
    JOIN genres ON genres.id = song_genres.genre_id
    JOIN users ON users.id = streams.user_id
    GROUP BY streams.user_id, genres.name
    ORDER BY streams.user_id DESC, stream_count DESC
)
SELECT username,
       COUNT(DISTINCT name) AS genres_listened_to
FROM top_genres_per_user
GROUP BY username;

-- RESULTS:
-- The number of genres listened to per user ranges from 6–23.

-- INTERPRETATION:
-- The range of genres listened to per user seems consistent
-- with the seeding code, which assigns 60% of a user's streams
-- to their favorite genres and 40% to random genres.
-- Since each user has 1 to 3 favorite genres and generates 25-100
-- streams, a range of 6-23 genres listened to seems aligned with
-- this bias.
------------------------------------------------------------------------------------

------------------------------------------------------------------------------------
-- *********** SONG ANALYTICS ***********
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** MOST STREAMED SONGS ***
------------------------------------------------------------------------------------
-- QUESTION:
-- Which songs have the highest stream counts?

-- QUERY:
SELECT songs.name, artists.name, COUNT(*) AS total_streams
FROM streams
JOIN songs ON songs.id = streams.song_id
JOIN song_credits ON song_credits.song_id = songs.id
JOIN artists ON artists.id = song_credits.artist_id
GROUP BY songs.id
ORDER BY total_streams DESC
LIMIT 10;

-- QUERY (Redone to avoid future stream multiplication):
WITH top_songs AS (
    SELECT song_id, COUNT(*) AS total_streams
    FROM streams
    GROUP BY song_id
)
SELECT ts.song_id,
       s.name AS Song,
       a.name AS Artist,
       ts.total_streams AS "Total Streams"
FROM top_songs ts
JOIN songs s ON ts.song_id=s.id
JOIN song_credits sc ON s.id=sc.song_id
JOIN artists a ON sc.artist_id = a.id
ORDER BY "Total Streams" DESC
LIMIT 10;

-- RESULTS:
-- The top 3 songs are:
-- 1. "Can't Help Falling in Love" by Elvis Presley (157 streams)
-- 2. "Shinunoga E-wa" by Fuji Kaze (71 streams)
-- 3. "Overdose" by なとり (70 streams)
-- The remaining 7 top songs have 47-60 total streams

-- INTERPRETATION:
-- Most top songs have relatively similar stream counts (47 to 71),
-- while "Can't Help Falling in Love" emerges as a significant outlier (157 streams).
-- This suggests the random generation process can still
-- produce organically dominant songs through repeated selection.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** MOST SKIPPED SONGS ***
------------------------------------------------------------------------------------
-- QUESTION:
-- Which songs have the highest skips? highest skip rates?

-- FOR HIGHEST SKIPS
-- QUERY:
SELECT songs.name, artists.name, COUNT(*) AS total_skips
FROM streams
JOIN songs ON songs.id = streams.song_id
JOIN song_credits ON song_credits.song_id = songs.id
JOIN artists ON artists.id = song_credits.artist_id
WHERE skipped = 1
GROUP BY songs.id
ORDER BY total_skips DESC
LIMIT 10;

-- FOR HIGHEST SKIP RATES
-- QUERY:
WITH
    total_skips AS (
        SELECT song_id, COUNT(*) AS total_skips
        FROM streams
        WHERE skipped = 1
        GROUP BY song_id
        ORDER BY total_skips DESC
),
    total_streams AS (
        SELECT song_id, COUNT(*) AS total_streams
        FROM streams
        GROUP BY song_id
        ORDER BY total_streams DESC
)
SELECT a.song_id,
       CAST(total_skips AS REAL) / total_streams AS skip_rate
FROM total_skips a
JOIN total_streams b ON a.song_id = b.song_id
-- Limit to songs with more than 2 streams
WHERE total_streams > 2
ORDER BY skip_rate DESC
LIMIT 10;

-- RESULTS:
-- The top 3 skipped songs by number of skips are:
-- 1. "Can't Help Falling in Love" by Elvis Presley (53 skips)
-- 2. "Angeleys" by ABBA (18 skips)
-- 3. "Last Last" by Burna Boy (17 skips)
-- The remaining 7 top skipped songs have 11-16 total skips.

-- OF SONGS WITH OVER 2 STREAMS:
-- The top 2 skipped songs by skip rate (skips/streams)
-- have a skip rate of 100%.
-- The following 5 songs have a skip rate of 75%.

-- INTERPRETATION:
-- Songs with the highest total skips largely overlap with
-- the most-streamed songs overall, suggesting exposure contributes
-- heavily to raw skip counts.
-- In contrast, skip-rate analysis highlights songs that are
-- disproportionately skipped relative to their stream volume.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** SONGS WITH HIGHEST AVERAGE COMPLETION RATE ***
------------------------------------------------------------------------------------
-- QUESTION:
-- Which songs do users liten to most fully?

-- QUERY:
SELECT songs.name,
       artists.name,
       AVG(CAST(ms_played AS REAL) / duration_ms) AS avg_completion_rate,
       COUNT(*) AS total_streams
FROM streams
JOIN songs ON songs.id = streams.song_id
JOIN song_credits ON song_credits.song_id = songs.id
JOIN artists ON artists.id = song_credits.artist_id
GROUP BY songs.id
HAVING COUNT(*) > 3
ORDER BY avg_completion_rate DESC
LIMIT 10;

-- RESULTS:
-- The top 3 most fully listened to songs by avg completion rate
-- with over 3 streams are:
-- 1. "Notion" by The Rare Occasions (0.828, 6 streams)
-- 2. "Cheating on You" by Charlie Puth (0.823, 4 streams)
-- 3. "Teeth" by 5 Seconds of Summer (0.814, 4 streams)
-- The remaining 7 top fully listened to songs have avg completion
-- rates ranging from 0.725 to 0.753 and have 4-8 streams.

-- INTERPRETATION:
-- Although the top 3 most fully listend to songs only have 4-6 streams,
-- their relatively high completion rates suggest that the random
-- generation process can still produce songs with higher completion
-- rates through repeated selection.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** SONGS WITH THE MOST REPEAT LISTENERS ***
------------------------------------------------------------------------------------
-- QUESTION:
-- What songs have the most repeat listeners?

-- QUERY:
WITH user_song_streams AS (
    SELECT song_id, user_id, COUNT(*) AS stream_count
    FROM streams
    -- Exclude skips
    WHERE skipped = 0
    GROUP BY song_id, user_id
),
    repeat_listeners AS (
    SELECT song_id, COUNT(*) AS repeat_listener_count
    FROM user_song_streams
    WHERE stream_count > 1
    GROUP BY song_id
)
SELECT songs.name, artists.name, r.repeat_listener_count
FROM repeat_listeners r
JOIN songs ON songs.id = r.song_id
JOIN song_credits ON song_credits.song_id = songs.id
JOIN artists ON artists.id = song_credits.artist_id
ORDER BY r.repeat_listener_count DESC
LIMIT 10;

-- RESULTS:
-- The top 7 songs with the most repeat listeners have 7 repeat listeners,
-- while the remaining 3 have 6 repeat listeners.
-- The top 3 are:
-- 1. "Stayin Alive" by Bee Gees
-- 2. "Never Gonna Give You Up" by Rick Astley
-- 3. "Shinunoga E-Wa" by Fuji Kaze
------------------------------------------------------------------------------------

------------------------------------------------------------------------------------
-- *********** GENRE ANALYTICS ***********
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** MOST POPULAR GENRES OVERALL ***
------------------------------------------------------------------------------------
-- QUESTION:
-- What are the top genres by total streams? by total listening time?

-- Top genres by total streams:
SELECT genres.name, COUNT(*) AS total_streams
FROM streams
JOIN song_genres ON song_genres.song_id = streams.song_id
JOIN genres ON genres.id = song_genres.genre_id
GROUP BY genres.id
ORDER BY total_streams DESC
LIMIT 10;

-- Top genres by total listening time
SELECT genres.name, SUM(ms_played) AS total_ms_played
FROM streams
JOIN song_genres ON streams.song_id = song_genres.song_id
JOIN genres ON song_genres.genre_id = genres.id
GROUP BY genres.id
ORDER BY total_ms_played DESC
LIMIT 10;

-- RESULTS:
-- The top 3 genres by total streams are:
-- 1. dance (323 streams)
-- 2. latino (292 streams)
-- 3. hard-rock (277 streams)

-- The top 3 genres by total listening time are:
-- 1. hard-rock (37815346  ms)
-- 2. dance (32155622 ms)
-- 3. alt-rock (30247406 ms)

-- INTERPERTATION
-- The slight disparity between rankings may be due to the top genres
-- by total listening time comprising longer songs on average.
-- i.e., because certain genres may consist of longer songs, they
-- may accumulate more listening time from users who prefer those genres.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** GENRES WITH HIGHEST SKIP RATES ***
------------------------------------------------------------------------------------
-- QUESTION:
-- Which genres have the highest skip rates? i.e., do users skip some genres more often?

-- QUERY:
WITH
    genre_skips AS (
        SELECT genres.name, COUNT(*) AS total_skips
        FROM streams
        JOIN song_genres ON streams.song_id = song_genres.song_id
        JOIN genres ON song_genres.genre_id = genres.id
        WHERE skipped = 1
        GROUP BY genres.id
        --ORDER BY total_skips DESC
),
    genre_streams AS (
        SELECT genres.name, COUNT(*) AS total_streams
        FROM streams
        JOIN song_genres ON streams.song_id = song_genres.song_id
        JOIN genres ON song_genres.genre_id = genres.id
        GROUP BY genres.id
        --ORDER BY total_streams DESC
    )
SELECT sk.name,
       CAST(total_skips AS REAL) / total_streams AS skip_rate
FROM genre_skips sk
JOIN genre_streams st ON sk.name = st.name
ORDER BY skip_rate DESC
LIMIT 10;

-- RESULS:

-- By TOTAL SKIPS, the top 3 most skipped genres are:
-- 1. latino (81 skips)
-- 2. dance (74 skips)
-- 3. hard-rock (60 skips)
-- The remaining most skipped genres range from 42 to 56 skips.

-- By SKIP RATE, the top 3 most skipped genres are:
-- 1. r-n-b (0.44)
-- 2. synth-pop (0.36)
-- 3. rock-n-roll (0.34)

-- NOTE:
-- The top 3 skipped genres by TOTAL STREAMS are also those
-- with the most streams (including skips).
-- Perhaps certain queries above should be modified to exclude skips when
-- tracking "top" categories.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** MOST POPULAR GENRES OVERALL ***
------------------------------------------------------------------------------------
-- PROMPT:
-- For each genre, find total_streams_per_genre / total_sreams

-- QUERY:
SELECT genres.name AS "Genre",
       CAST(COUNT(*) AS REAL) / (
           SELECT COUNT(*)
           FROM streams
           WHERE skipped = 0) AS "Genre Share"
FROM streams
JOIN song_genres sg ON streams.song_id = sg.song_id
JOIN genres ON sg.genre_id = genres.id
WHERE skipped = 0
GROUP BY sg.genre_id;
------------------------------------------------------------------------------------

------------------------------------------------------------------------------------
-- *********** TIME-BASED ANALYTICS ***********
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** MOST ACTIVE LISTENING HOURS ***
------------------------------------------------------------------------------------
-- QUESTION: At what hours does the platform see the most streams?

-- QUERY:
SELECT strftime('%H', start_datetime) AS hour, COUNT(*) AS total_streams
FROM streams
GROUP BY hour
ORDER BY total_streams DESC;

-- RESULTS:
-- The most popular streaming hours are 9am - 2pm, with each hour
-- ranging from 492-527 streams.
-- The next most popular streaming hours are 8pm - 1 am, with each hour
-- ranging from 280-330 streams.
-- The least popular hours are 8 am, 2 am, and 3 am.

-- INTERPRETATION:
-- Streams are strongly concentrated within the seeded
-- day (9am–2pm) and night (8pm–1am) activity windows,
-- indicating that the active-hours preference model
-- is influencing listening behavior as intended.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** DAY VS NIGHT LISTENING BEHAVIOR ***
------------------------------------------------------------------------------------
-- QUESTION:
-- How do average skip rate, average completion rate, and top genres
-- compare between day and night hours?

-- QUERY:
-- (CTEs are named as "day" but actually include day and night)

WITH
    day_skips AS (
        SELECT strftime('%H', start_datetime) AS hour,
            COUNT(*) FILTER (WHERE skipped = 1) AS total_skips,
            COUNT(*) AS total_streams
        FROM streams
        WHERE hour IN ('09', '10', '11', '12', '13', '14',
                       '20', '21', '22', '23', '00', '01')
        GROUP BY hour
        ORDER BY hour ASC
    ),
    day_skip_rate AS (
        SELECT hour, CAST(total_skips AS REAL) / total_streams AS skip_rate
        FROM day_skips
    ),
    day_completion_rate AS (
        SELECT strftime('%H', start_datetime) AS hour,
               AVG(CAST(ms_played AS REAL) / duration_ms) AS completion_rate
        FROM streams
        JOIN songs ON streams.song_id = songs.id
        WHERE hour IN ('09', '10', '11', '12', '13', '14',
                       '20', '21', '22', '23', '00', '01')
        GROUP BY hour
        ORDER BY hour ASC
    ),
    day_genres AS (
        SELECT strftime('%H', start_datetime) AS hour,
               genres.name AS genre,
               COUNT(*) AS total_streams
        FROM streams
        JOIN songs ON streams.song_id = songs.id
        JOIN song_genres ON songs.id = song_genres.song_id
        JOIN genres ON song_genres.genre_id = genres.id
        WHERE hour IN ('09', '10', '11', '12', '13', '14',
                       '20', '21', '22', '23', '00', '01')
        GROUP BY hour, genres.id
        ORDER BY hour ASC, total_streams DESC
    ),
    day_top_genres AS (
        SELECT hour, genre AS top_genre
        FROM day_genres
        GROUP by hour
    )
SELECT dsr.hour,
       ROUND(dsr.skip_rate, 2) AS skip_rate,
       ROUND(dcr.completion_rate, 2) AS completion_rate,
       dtg.top_genre
FROM day_skip_rate dsr
JOIN day_completion_rate dcr ON dsr.hour = dcr.hour
JOIN day_top_genres dtg ON dcr.hour = dtg.hour;

-- RESULTS:
-- From 9am-2pm:
-- * skip rates range from 0.20 to 0.25
-- * completion rates range from 0.45 to 0.47
-- * top genres include: hard-rock, dance, latino
-- From 8pm-1am:
-- * skip rates range from 0.18 to 0.26
-- * completion rates range from 0.45 to 0.50
-- * top genres include: pop, dance, latino

-- INTERPRETATION:
-- Listening behavior is relatively similar during both
-- seeded day and night windows, though certain genre
-- preferences differ slightly by time period.
-- Dance and latino remain dominant across both intervals,
-- while hard-rock appears more frequently during daytime hours
-- and pop appears more frequently during nighttime hours.

-- NOTE:
-- To improve realistic streaming behavior, the code for generating
-- streams can be altered to favor certain genres at different times.
-- For example, increasing the probability of r&b streams at night.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** STREAM TRENDS OVER TIME ***
------------------------------------------------------------------------------------
-- QUESTION:
-- How many streams have been made in the past day, week, and month?

-- QUERY:
WITH
    past_day_streams AS (
        SELECT 'blank' AS blank,
               COUNT(*) AS past_day_streams
        FROM streams
        WHERE start_datetime >= DATE('now', '-2 days', 'localtime')
    ),
    past_week_streams AS (
        SELECT 'blank' AS blank,
               COUNT(*) AS past_week_streams
        FROM streams
        WHERE start_datetime >= DATE('now', '-9 days', 'localtime')
    ),
    past_month_streams AS (
        SELECT 'blank' AS blank,
               COUNT(*) AS past_month_streams
        FROM streams
        WHERE start_datetime >= DATE('now', '-32 days', 'localtime')
    ),
    past_year_streams AS (
        SELECT 'blank' AS blank,
               COUNT(*) AS past_year_streams
        FROM streams
        WHERE start_datetime >= DATE('now', '-367 days', 'localtime')
    )
SELECT pds.past_day_streams,
       pws.past_week_streams,
       pms.past_month_streams,
       pys.past_year_streams
FROM past_day_streams pds
JOIN past_week_streams pws ON pds.blank = pws.blank
JOIN past_month_streams pms ON pws.blank = pms.blank
JOIN past_year_streams pys ON pms.blank = pys.blank;

-- Streams older than one year
SELECT COUNT(*) AS older_streams
FROM streams
WHERE start_datetime < DATE('now', '-367 days');

-- NOTE:
-- The current date is May 22.
-- However, "streams" was seeded on May 20, 2026,
-- so the above queries assume the current date is May 20.

-- RESULTS:
-- Past day: 77 total streams
-- Past week: 627 total streams
-- Past month: 2517 streams
-- Past year: 4634 streams
-- Older than one year: 1162 streams

-- INTERPRETATION:
-- Most streams are concentrated within the past month and year,
-- reflecting the generator's recency bias toward newer streams.
-- Only a smaller fraction of streams are older than one year,
-- producing a more realistic temporal distribution than a
-- uniform spread across all years.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** LISTENING TIME ANALYTICS (FOR STREAMLIT) ***
------------------------------------------------------------------------------------
-- STREAMS BY HOUR
-- AVG USER ACTIVITY BY HOUR
-- AVG COMPLETION RATE BY HOUR
-- AVG SKIP RATE BY HOUR

-- NOTE: user_listening_hours includes skips as streams

SELECT hour AS "Hour of Day",
       SUM(total_streams) AS "Total Streams",
       AVG(hour_share) AS "Avg Hour Share",
       AVG(avg_completion_rate) AS "Avg Completion Rate",
       AVG(skip_rate) AS "Avg Skip Rate"
FROM user_listening_hours
GROUP BY hour
ORDER BY hour;
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- ******* RECOMMENDATION-ORIENTED QUERIES *******
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** CANDIDATE LIKED SONGS ***
------------------------------------------------------------------------------------
-- Find user-song pairs where:
-- * stream count is high
-- * AND completion rate is high

-- QUERY:
WITH
    stream_count AS (
        -- Exclude skips
        SELECT user_id, song_id, COUNT(*) AS total_streams
        FROM streams
        WHERE skipped = 0
        GROUP BY user_id,song_id
        ORDER BY total_streams DESC, user_id ASC
),
    high_stream_count AS (
        SELECT user_id, song_id
        FROM stream_count
        WHERE total_streams > 4
),
    completion_rate AS (
        SELECT user_id,
               song_id,
               AVG(CAST(ms_played AS REAL) / duration_ms) AS completion_rate,
               COUNT(*) AS total_streams
        FROM streams
        JOIN songs ON songs.id = streams.song_id
        WHERE skipped = 0
        GROUP BY user_id, song_id
        ORDER BY completion_rate DESC
),
    high_completion_rate AS (
        SELECT user_id, song_id
        FROM completion_rate
        WHERE completion_rate > 0.6
),
    liked_songs AS (
        SELECT * FROM high_stream_count
        INTERSECT
        SELECT * FROM high_completion_rate
    )
SELECT user_id, ls.song_id, songs.name, artists.name
FROM liked_songs ls
JOIN songs ON ls.song_id = songs.id
join song_credits sc ON songs.id = sc.song_id
join artists ON sc.artist_id = artists.id
ORDER BY user_id ASC, ls.song_id ASC;

-- RESULTS:
-- 9 candidate liked songs from 8 distinct users, where a candidate liked song
-- is one played by over 4 times by a user with an average
-- completion rate of over 70%.
-- When the average completion rate threshold is lowered to 60%,
-- thee are 47 candidate liked songs.

-- INTERPRETATION:
-- Candidate liked songs are relatively rare under stricter thresholds,
-- suggesting that repeated listening combined with high completion rates
-- is uncommon behavior.
-- Lowering the completion-rate threshold substantially increases the
-- number of candidate liked songs, indicating the recommendation criteria
-- are highly sensitive to completion-rate requirements.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** USER FAVORITE SONGS ***
------------------------------------------------------------------------------------
-- Find each user's top 3 most replayed songs

-- QUERY:
WITH
    replay_count AS (
        SELECT user_id,
               song_id,
               COUNT(*) AS total_streams
        FROM streams
        GROUP BY user_id,song_id
        ORDER BY user_id ASC, total_streams DESC
),
    favorite_songs AS (
        SELECT *,
               ROW_NUMBER() OVER (
                   PARTITION BY user_id
                   ORDER BY total_streams DESC
                ) AS rn
        FROM replay_count
)
SELECT user_id, fs.song_id, s.name, a.name, total_streams
FROM favorite_songs fs
JOIN songs s ON fs.song_id = s.id
JOIN song_credits sc ON s.id=sc.song_id
JOIN artists a ON sc.artist_id=a.id
WHERE rn <= 3
ORDER BY user_id ASC, fs.song_id ASC;

-- RESULTS:
-- Users' top 3 replayed songs vary from 1 to 60 total streams
-- and seem reasonably varied.

-- INTERPRETATION:
-- High replay counts for certain songs may result from users'
-- favorite genres containing relatively small song pools,
-- increasing the probability of repeated selection.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** USER SIMILARITY ***
------------------------------------------------------------------------------------
-- Find pairs of users who listen to similar genres

-- QUERY:
-- Currently unsure how to approach user pairs with SQLite,
-- so I grouped by top_genres to see groups of users who
-- share the same top genre.

WITH
    genre_counts AS (
        SELECT users.username,
            genres.name AS genre,
            COUNT(*) AS stream_count,
            ROW_NUMBER() OVER (
                    PARTITION BY users.id
                    ORDER BY COUNT(*) DESC
            ) AS rn
        FROM streams
        JOIN song_genres ON song_genres.song_id = streams.song_id
        JOIN genres ON genres.id = song_genres.genre_id
        JOIN users ON users.id = streams.user_id
        GROUP BY users.id, genres.id
)
SELECT username, genre, stream_count
FROM genre_counts
-- Selecting the top 3 genres per each user
WHERE rn <= 3
ORDER BY genre ASC;

-- RESULTS:
-- Most top genres seem to have 3-5 users,
-- with several only having more or only one.

-- INTERPRETATION:
-- Users appear reasonably distributed across top genres,
-- with most genres shared by small groups of users rather
-- than dominated by the entire platform.
-- This suggests the synthetic preference model produces
-- differentiated listening behavior instead of overly uniform tastes.
------------------------------------------------------------------------------------

------------------------------------------------------------------------------------
-- ******* DATA QUALITY / REALISM ANALYTICS *******
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** DISTRIBUTION OF STREAM COUNTS ***
------------------------------------------------------------------------------------
-- AVERAGE, MIN, MAX:
-- Find the average, min, and max number of stream counts per user

WITH user_streams AS (
    SELECT user_id, COUNT(*) AS total_streams
    FROM streams
    GROUP BY user_id
    ORDER BY user_id ASC
)
SELECT AVG(total_streams),
       MIN(total_streams),
       MAX(total_streams)
FROM user_streams;

-- RESULTS:
-- AVG: 57.86 total streams.
-- MIN: 25 total streams
-- MAX: 99 total streams

-- INTERPRETATION:
-- Stream counts align with the seeding constraint of
-- 25–100 streams per user and appear reasonably dispersed
-- across that range, avoiding excessive concentration around
-- a single activity level.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** DISTRIBUTION OF COMPLETION RATIOS ***
------------------------------------------------------------------------------------
-- QUESTION:
-- Are most streams skips? near-complete? uniformly random?
-- What does the distribution imply?

-- QUERY:
WITH completion_rates AS (
    SELECT ROUND(CAST(ms_played AS REAL) /
           duration_ms, 2) AS completion_rate
    FROM streams
    JOIN songs ON streams.song_id = songs.id
    ORDER BY completion_rate DESC
)
SELECT completion_rate,
       COUNT(*) AS frequency,
       ROUND(CAST(COUNT(*) AS REAL) * 100 /
       (SELECT COUNT(*) FROM completion_rates), 2) AS percentage
FROM completion_rates
GROUP BY completion_rate
ORDER BY frequency DESC, completion_rate DESC;

-- RESULTS:
-- The frequency of completion rates seems reasonably varied,
-- which no specific completion rate dominating the others.
-- Each completion rate comprises 0.48 to 2.04 percent of all
-- completion rates, with a completion rate of 10% being the most
-- frequent and a completion rate of 100% being the least.

-- INTERPRETATION
-- Completion ratios are broadly distributed rather than concentrated
-- around a few dominant values, suggesting users exhibit varied
-- listening behavior instead of highly repetitive stream patterns.
-- Lower completion ratios are slightly more common than full listens,
-- which is consistent with the inclusion of skips and partial playback
-- in the stream generation model.
------------------------------------------------------------------------------------

------------------------------------------------------------------------------------
-- ******* FOR SEEDING LIKED SONGS *******
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** CANDIDATE LIKED SONGS VIEW (REFINED) ***
------------------------------------------------------------------------------------
-- PROMPT:
-- Aggregate per (user_id, song_id):
---Compute:
---- * stream_count
---- * avg_completion_rate
---- * total_ms_played

-- QUERY:
CREATE VIEW IF NOT EXISTS candidate_metrics AS
SELECT user_id,
       song_id,
       COUNT(*) AS total_streams,
       SUM(ms_played) AS total_ms_played,
       AVG(CAST(ms_played AS REAL) / duration_ms) AS completion_rate,
       MAX(start_datetime) AS latest_stream
FROM streams
JOIN songs ON streams.song_id = songs.id
WHERE skipped = 0 -- Exclude skips
GROUP BY user_id, song_id
ORDER BY user_id ASC, song_ID ASC;
------------------------------------------------------------------------------------

