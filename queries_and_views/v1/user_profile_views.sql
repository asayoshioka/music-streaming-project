------------------------------------------------------------------------------------
-- USER PROFILE VIEWS
------------------------------------------------------------------------------------
-- Views for constructing user profiles that include:
-- top genres, top artists, behavior, listening hours
------------------------------------------------------------------------------------

------------------------------------------------------------------------------------
-- USER GENRE AFFINITY VIEW
------------------------------------------------------------------------------------
-- COLUMNS:
-- user_id, genre_id, genre, normalized_streams,
-- normalized_replays, avg_completion_rate, affinity_score
-- * normalized_streams = total_streams_per_genre / max_total_streams_per_genre
-- * normalzied_replays = avg_streams_per_song / max_avg_streams_per_song,
-- * where avg_streams_per_song = total streams per genre / distinct songs per genre
-- * affinity_score = 0.6 * normalized_streams +
--                    0.2 normalized_replays +
--                    0.2 avg_completion_rate

-- NOTE:
-- Here, streams exclude skips.
-- The candidate_metrics VIEW already excludes skips.

CREATE VIEW user_genre_affinity AS
WITH
    user_streamed_genres AS (
        -- Note: Each song in the database currently maps to
        -- exactly one genre, making this JOIN clause valid.
        SELECT user_id,
               sg.genre_id,
               SUM(total_streams) AS total_streams,
               COUNT(DISTINCT cm.song_id) AS distinct_songs,
               AVG(completion_rate) AS avg_completion_rate,
               CAST(SUM(total_streams) AS REAL) / COUNT(DISTINCT cm.song_id) AS avg_streams_per_song
        FROM candidate_metrics cm
        JOIN song_genres sg ON cm.song_id = sg.song_id
        GROUP BY user_id, sg.genre_id
),
    max_metrics AS (
        SELECT user_id,
               MAX(total_streams) AS max_total_streams,
               MAX(avg_streams_per_song) AS max_avg_streams_per_song
        FROM user_streamed_genres
        GROUP BY user_id
),
    normalized_metrics AS (
        SELECT usg.user_id,
               genre_id,
               CAST(total_streams AS REAL) /
                    max_total_streams AS normalized_streams,
               CAST(avg_streams_per_song AS REAL) /
                    max_avg_streams_per_song AS normalized_replays,
               avg_completion_rate
        FROM user_streamed_genres usg
        JOIN max_metrics mm ON usg.user_id = mm.user_id
)
SELECT user_id,
       genre_id,
       genres.name AS genre,
       normalized_streams,
       normalized_replays,
       avg_completion_rate,
       (0.6 * normalized_streams +
        0.2 * normalized_replays +
        0.2 * avg_completion_rate) AS affinity_score
FROM normalized_metrics nm
JOIN genres ON nm.genre_id = genres.id
ORDER BY user_id ASC, affinity_score DESC;
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- USER ARTIST AFFINITY VIEW
------------------------------------------------------------------------------------
-- COLUMNS:
-- user_id, artist_id, artist, normalized_streams, normalized_replays,
-- avg_completion_rate, affinity_score
-- * normalized_streams = total_streams_per_artist / max_total_streams_per_artist
-- * normalzied_replays = avg_streams_per_song / max_avg_streams_per_song,
--   where avg_streams_per_song = total streams per artist / distinct songs per artist
-- * affinity_score = 0.6 * normalized_streams +
--                    0.2 normalized_replays +
--                    0.2 avg_completion_rate

-- NOTE:
-- Here, streams exclude skips.
-- The candidate_metrics VIEW already excludes skips.

CREATE VIEW user_artist_affinity AS
WITH
    user_streamed_artists AS (
        -- Note: Each song in the database currently maps to
        -- exactly one artist, making this JOIN clause valid.
        SELECT user_id,
               sc.artist_id,
               SUM(total_streams) AS total_streams,
               COUNT(DISTINCT cm.song_id) AS distinct_songs,
               AVG(completion_rate) AS avg_completion_rate,
               CAST(SUM(total_streams) AS REAL) / COUNT(DISTINCT cm.song_id) AS avg_streams_per_song
        FROM candidate_metrics cm
        JOIN song_credits sc ON cm.song_id = sc.song_id
        GROUP BY user_id, sc.artist_id
),
    max_metrics AS (
        SELECT user_id,
               MAX(total_streams) AS max_total_streams,
               MAX(avg_streams_per_song) AS max_avg_streams_per_song
        FROM user_streamed_artists
        GROUP BY user_id
),
    normalized_metrics AS (
        SELECT usa.user_id,
               artist_id,
               CAST(total_streams AS REAL) /
                    max_total_streams AS normalized_streams,
               CAST(avg_streams_per_song AS REAL) /
                    max_avg_streams_per_song AS normalized_replays,
               avg_completion_rate
        FROM user_streamed_artists usa
        JOIN max_metrics mm ON usa.user_id = mm.user_id
)
SELECT user_id,
       artist_id,
       artists.name AS artist,
       normalized_streams,
       normalized_replays,
       avg_completion_rate,
       (0.6 * normalized_streams +
        0.2 * normalized_replays +
        0.2 * avg_completion_rate) AS affinity_score
FROM normalized_metrics nm
JOIN artists ON nm.artist_id = artists.id
ORDER BY user_id ASC, affinity_score DESC;

------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- USER DIVERSITY METRICS VIEW
------------------------------------------------------------------------------------
-- COLUMNS:
-- user_id, total_streams, distinct_genres, diversity_score, dominant_genre_share
-- * dominant_genre_share = max genre proportion per user
-- * (diversity_score explained below)

-- DIVERSITY SCORE:
-- STEP 1:
-- Compute genre proportions per user:
-- genre_share = genre_streams / toal_user_streams
-- STEP 2: USE SIMPSON DIVERSITY INDEX
-- (proposed by ChatGPT as an easy and interpretable method)
-- Formula: 1 - sum(p_i ^ 2), where p_i = genre_proportion

-- WORKFLOW:
-- 1) compute total streams
-- 2) compute streams per genre
-- 3) compute genre proportions
-- 4) compute 1 - sum(p_i ^ 2)

-- NOTE:
-- Here, streams exclude skips.
-- The candidate_metrics VIEW already excludes skips.

CREATE VIEW user_diversity_metrics AS
WITH
    total_streams AS (
        SELECT user_id,
               SUM(total_streams) AS total_streams,
               COUNT(DISTINCT genre_id) AS distinct_genres
        FROM candidate_metrics cm
        JOIN song_genres sg ON cm.song_id = sg.song_id
        GROUP BY user_id
    ),
    genre_streams AS (
        SELECT user_id,
               genre_id,
               SUM(total_streams) AS genre_streams
        FROM candidate_metrics cm
        JOIN song_genres sg ON cm.song_id = sg.song_id
        GROUP BY user_id, genre_id
    ),
    genre_proportions AS (
        SELECT gs.user_id,
               genre_id,
               CAST(genre_streams AS REAL) /
                   ts.total_streams AS genre_proportion
        FROM genre_streams gs
        JOIN total_streams ts ON gs.user_id = ts.user_id
    ),
    max_genre_proportions AS (
        SELECT user_id,
               MAX(genre_proportion) AS dominant_genre_share
        FROM genre_proportions
        GROUP BY user_id
    ),
    diversity_score AS (
        SELECT user_id,
               (1 - SUM(genre_proportion * genre_proportion))
               AS diversity_score
        FROM genre_proportions
        GROUP BY user_id
    )
SELECT ts.user_id,
       ts.total_streams,
       ts.distinct_genres,
       ds.diversity_score,
       mgp.dominant_genre_share
FROM total_streams ts
JOIN diversity_score ds ON ts.user_id = ds.user_id
JOIN max_genre_proportions mgp ON ds.user_id = mgp.user_id;
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- USER LISTENING HOURS VIEW
------------------------------------------------------------------------------------
-- COLUMNS:
-- user_id, hour, total_streams, total_ms_played, avg_completion_rate, skip_rate,
-- * hour_share = (streams during hour / total user streams)

CREATE VIEW user_listening_hours AS
WITH user_total_streams AS (
    SELECT user_id,
           COUNT(*) AS total_streams
    FROM streams
    GROUP BY user_id
)
SELECT s.user_id,
       strftime('%H', start_datetime) AS hour,
       COUNT(*) AS total_streams,
       SUM(ms_played) AS total_ms_played,
       ROUND(AVG(CAST(ms_played AS REAL) /
           songs.duration_ms), 3) AS avg_completion_rate,
       ROUND(CAST(COUNT(CASE WHEN skipped = 1 THEN 1 END) AS REAL) /
           COUNT(*), 3) AS skip_rate,
       ROUND(CAST(COUNT(*) AS REAL) /
           uts.total_streams, 3) AS hour_share
FROM streams s
JOIN songs ON s.song_id = songs.id
JOIN user_total_streams uts ON s.user_id = uts.user_id
GROUP BY s.user_id, hour;
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- USER BEHAVIOR METRICS VIEW
------------------------------------------------------------------------------------
-- COLUMNS:
-- user_id, total_streams, total_listening_time_ms, avg_completion_rate,
-- skip_rate, avg_streams_per_song, distinct_songs, distinct_artists,
-- distinct_genres, avg_session_length (FUTURE)

CREATE VIEW user_behavior_metrics AS
WITH
    base_metrics AS (
        SELECT user_id,
               COUNT(*) AS total_streams,
               SUM(ms_played) AS total_listening_time_ms,
               AVG(CAST(ms_played AS REAL) /
                   songs.duration_ms) AS avg_completion_rate,
               CAST(COUNT(CASE WHEN skipped = 1 THEN 1 END) AS REAL) /
                   COUNT(*) AS skip_rate,
               CAST(COUNT(*) AS REAL) /
                   COUNT(DISTINCT streams.song_id) AS avg_streams_per_song,
               COUNT(DISTINCT streams.song_id) AS distinct_songs
        FROM streams
        JOIN songs ON streams.song_id = songs.id
        GROUP BY user_id
    ),
    artist_counts AS (
        SELECT user_id,
               COUNT(DISTINCT sc.artist_id) AS distinct_artists
        FROM streams s
        JOIN song_credits sc ON s.song_id = sc.song_id
        GROUP BY user_id
    ),
    genre_counts AS (
        SELECT user_id,
               COUNT(DISTINCT sg.genre_id) AS distinct_genres
        FROM streams s
        JOIN song_genres sg ON s.song_id = sg.song_id
        GROUP BY user_id
    )
SELECT bm.user_id,
       bm.total_streams,
       bm.total_listening_time_ms,
       ROUND(bm.avg_completion_rate, 3) AS avg_completion_rate,
       ROUND(bm.skip_rate, 3) AS skip_rate,
       ROUND(bm.avg_streams_per_song, 2) AS avg_streams_per_song,
       bm.distinct_songs,
       ac.distinct_artists,
       gc.distinct_genres
FROM base_metrics bm
JOIN artist_counts ac ON bm.user_id = ac.user_id
JOIN genre_counts gc ON bm.user_id = gc.user_id
ORDER BY bm.user_id ASC;
------------------------------------------------------------------------------------
-- NOTE:
-- The user_genre_affinity, user_artist_affinity, and
-- user_diversity_metrics views are intended to model
-- user preference and long-term taste.
-- Therefore, these views exclude skipped streams and focus only
-- on meaningful engagement.

-- In contrast, the user_listening_hours and
-- user_behavior_metrics views are intended to model
-- overall listening behavior.
-- Therefore, these views include skipped streams,
-- since skipping behavior itself is behaviorally meaningful.
------------------------------------------------------------------------------------
