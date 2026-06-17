------------------------------------------------------------------------------------
-- RECOMMENDATION QUERIES
------------------------------------------------------------------------------------

------------------------------------------------------------------------------------
-- ********** SIMPLE RECOMMENDATIONS **********
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- *** "USERS WHO LIKED X ALSO LIKED Y" ***
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- SONG RECOMMENDATIONS BASED ON LIKED SONGS OVERLAP
------------------------------------------------------------------------------------
-- QUESTION:
-- What songs are commonly liked by users who liked the most liked song?

-- THOUGHT-PROCESS:
-- * Find users who liked the target song
-- * Find other songs like by those users
-- * Rank/filter those songs somehow

-- QUERY:
WITH
    popular_liked_songs AS (
        SELECT song_id,
               COUNT(*) AS total_likes
        FROM liked_songs
        GROUP BY song_id
    ),
    users_who_liked_top_song AS (
        SELECT *
        FROM liked_songs
        WHERE song_id = (
            SELECT song_id
            FROM popular_liked_songs
            ORDER BY total_likes DESC
            LIMIT 1
        )
    ),
    user_threshold AS (
        SELECT (COUNT(DISTINCT user_id) * 0.3) AS threshold
        FROM users_who_liked_top_song
    ),
    users_other_liked_songs AS (
        SELECT user_id, song_id
        FROM liked_songs
        WHERE user_id IN (
            SELECT user_id
            FROM users_who_liked_top_song
        )
        -- Exclude the original shared liked song
        AND song_id != (
            SELECT song_id
            FROM popular_liked_songs
            ORDER BY total_likes DESC
            LIMIT 1
        )
    ),
    shared_liked_songs AS (
        SELECT song_id,
               COUNT(*) AS shared_likes
        FROM users_other_liked_songs
        GROUP BY song_id
    )
SELECT song_id
FROM shared_liked_songs
WHERE shared_likes >= (
    SELECT threshold
    FROM user_threshold
);

-- RESULTS:
-- Currently no overlapping liked songs by user's who liked the
-- most liked song. This is expected given the relatively small set of liked songs.

------------------------------------------------------------------------------------
-- SONG RECOMMENDATIONS BASED ON STREAM OVERLAP
------------------------------------------------------------------------------------
-- QUESTION:
-- What songs are commonly streamed by users who streamed
-- the most streamed song (exluding skips)?

-- NOTE:
-- The "candidate_metrics" contains the following columns:
-- user_id, song_id, total_streams, total_ms_played,
-- completion_rate (as a user's avg), and latest stream.
-- The view aleady excludes skips.

-- QUERY:
WITH
    popular_streamed_songs AS (
        SELECT song_id, SUM(total_streams) AS total_streams, AVG(completion_rate) AS avg_completion_rate
        FROM candidate_metrics
        GROUP BY song_id
        HAVING SUM(total_streams) > 10 AND AVG(completion_rate) > 0.5
),
    cohort_who_streamed_top_song AS (
        SELECT user_id
        FROM candidate_metrics
        WHERE song_id = (
            SELECT song_id
            FROM popular_streamed_songs
            ORDER BY total_streams DESC
            LIMIT 1
        )
),
    cohort_threshold AS (
        SELECT (COUNT(DISTINCT user_id) * 0.3) AS threshold -- low threshold to allow for query results
        FROM cohort_who_streamed_top_song
),
    cohort_other_streamed_songs AS (
        SELECT song_id
        FROM candidate_metrics
        WHERE user_id IN (
            SELECT user_id
            FROM cohort_who_streamed_top_song
        )
        -- Exclude the original shared streamed song
        AND song_id != (
            SELECT song_id
            FROM popular_streamed_songs
            ORDER BY total_streams DESC
            LIMIT 1
        )
),
    cohort_shared_streamed_songs AS (
        SELECT song_id, COUNT(*) AS shared_users
        FROM cohort_other_streamed_songs
        GROUP BY song_id
)
SELECT *
FROM cohort_shared_streamed_songs
WHERE shared_users >= (
    SELECT threshold
    FROM cohort_threshold
);

-- RESULTS:
-- Of the cohort who streamed the most streamed songs, there are 2 songs
-- with 3 shared users (i.e., with number of shared users greater than or equal to
-- 30% of the cohort).
------------------------------------------------------------------------------------

------------------------------------------------------------------------------------
-- ********** RESUABLE RECOMMENDATION TEMPLATES **********
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- SONG RECOMMENDATIONS RANKED BY OVERLAP
------------------------------------------------------------------------------------
-- PROMPT:
-- Given a song id, return related songs ranked by overlap.
------------------------------------------------------------------------------------
-- QUERY (WITHOUT SIMILARITY SCORE):
------------------------------------------------------------------------------------
WITH
    cohort_who_streamed_song AS (
        SELECT user_id
        FROM candidate_metrics
        WHERE song_id = ?
),
    cohort_threshold AS (
        SELECT (COUNT(DISTINCT user_id) * 0.3) AS threshold
        FROM cohort_who_streamed_song
),
    cohort_other_streamed_songs AS (
        SELECT song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id IN (
            SELECT user_id
            FROM cohort_who_streamed_song
        )
        -- Exclude the original shared streamed song
        AND song_id != ?
),
    cohort_shared_streamed_songs AS (
        SELECT song_id,
               COUNT(*) AS shared_users,
               AVG(total_streams) AS avg_streams_per_user,
               AVG(completion_rate) AS avg_completion_rate
        FROM cohort_other_streamed_songs
        GROUP BY song_id
)
SELECT *
FROM cohort_shared_streamed_songs
WHERE shared_users >= (
    SELECT threshold
    FROM cohort_threshold
)
AND avg_streams_per_user > 2
AND avg_completion_rate > 0.5
ORDER BY shared_users DESC,
         avg_completion_rate DESC,
         avg_streams_per_user DESC;

------------------------------------------------------------------------------------
-- QUERY (IMPROVED -- WITH SIMILARITY SCORE)
------------------------------------------------------------------------------------
-- SCORING SYSTEM:

-- score = (shared_users weight) + (completion weight) + (replay weight)

-- TO COMPUTE:

-- 1. Normalize metrics to similar ranges (i.e., between 0 and 1)
-- * normalized_shared = shared_users / max_shared_users
-- * normalized_replays = avg_streams_per_user / max_avg_streams
-- * avg_completion_rate is already naturally between 0 and 1

-- 2. similarity_score = 0.6 * normalized_shared + 0.2 * normalized_replays + 0.2 * avg_completion_rate

WITH
    cohort_who_streamed_song AS (
        SELECT user_id
        FROM candidate_metrics
        WHERE song_id = ?
),
    cohort_threshold AS (
        SELECT (COUNT(DISTINCT user_id) * 0.3) AS threshold
        FROM cohort_who_streamed_song
),
    cohort_other_streamed_songs AS (
        SELECT song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id IN (
            SELECT user_id
            FROM cohort_who_streamed_song
        )
        -- Exclude the original shared streamed song
        AND song_id != ?
),
    cohort_shared_streamed_songs AS (
        SELECT song_id,
               COUNT(*) AS shared_users,
               AVG(total_streams) AS avg_streams_per_user,
               AVG(completion_rate) AS avg_completion_rate
        FROM cohort_other_streamed_songs
        GROUP BY song_id
        -- Only include songs shared by a certain percentage of the cohort
        HAVING shared_users >= (
            SELECT threshold
            FROM cohort_threshold
        )
),
    normalized_metrics AS (
        SELECT song_id,
               CAST(shared_users AS REAL) / (
                    SELECT MAX(shared_users)
                    FROM cohort_shared_streamed_songs
                    ) AS normalized_shared,
               CAST(avg_streams_per_user AS REAL) / (
                    SELECT MAX(avg_streams_per_user)
                    FROM cohort_shared_streamed_songs
                    ) AS normalized_replays,
                avg_completion_rate
        FROM cohort_shared_streamed_songs
)
SELECT song_id,
       normalized_shared,
       normalized_replays,
       avg_completion_rate,
      (0.6 * normalized_shared +
       0.2 * normalized_replays +
       0.2 * avg_completion_rate) AS similarity_score
FROM normalized_metrics
ORDER BY similarity_score DESC;
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- SAME QUERY AS ABOVE WITHOUT THRESHOLD
------------------------------------------------------------------------------------
WITH
    cohort_who_streamed_song AS (
        SELECT user_id
        FROM candidate_metrics
        WHERE song_id = ?
),
    cohort_other_streamed_songs AS (
        SELECT song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id IN (
            SELECT user_id
            FROM cohort_who_streamed_song
        )
        -- Exclude the original shared streamed song
        AND song_id != ?
),
    cohort_shared_streamed_songs AS (
        SELECT song_id,
               COUNT(*) AS shared_users,
               AVG(total_streams) AS avg_streams_per_user,
               AVG(completion_rate) AS avg_completion_rate
        FROM cohort_other_streamed_songs
        GROUP BY song_id
),
    normalized_metrics AS (
        SELECT song_id,
               shared_users,
               avg_streams_per_user,
               CAST(shared_users AS REAL) / (
                    SELECT MAX(shared_users)
                    FROM cohort_shared_streamed_songs
                    ) AS normalized_shared,
               CAST(avg_streams_per_user AS REAL) / (
                    SELECT MAX(avg_streams_per_user)
                    FROM cohort_shared_streamed_songs
                    ) AS normalized_replays,
                avg_completion_rate
        FROM cohort_shared_streamed_songs
)
SELECT nm.song_id,
       songs.name,
       artists.name,
       shared_users,
       avg_streams_per_user,
       avg_completion_rate,
      (0.6 * normalized_shared +
       0.2 * normalized_replays +
       0.2 * avg_completion_rate) AS similarity_score
FROM normalized_metrics nm
JOIN songs ON nm.song_id = songs.id
JOIN song_credits sc ON songs.id=sc.song_id
JOIN artists ON sc.artist_id=artists.id
ORDER BY similarity_score DESC;
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- USER-TO-USER SIMILARITY
------------------------------------------------------------------------------------
-- GOAL:
-- Find users with similar listening behavior.

-- IDEA:
-- Compare users based on overlapping streamed songs.

-- PROMPT:
-- Given a user id, find the most similar users based on overlapping streamed songs.
-- For each candidate user, include:
-- * shared_song_count
-- * avg_replays_on_shared_songs
-- * avg_completion_on_shared_songs

-- QUERY:
WITH
    user_streamed_songs AS (
        SELECT song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id = ? AND
        -- Filter out streams with low engagement
              total_streams >= 2 AND
              completion_rate >= 0.5
    ),
    cohort_with_shared_streamed_songs AS (
        SELECT user_id, song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id != ? AND
              song_id IN (
                SELECT song_id
                FROM user_streamed_songs
              ) AND
              -- Filter out streams with low engagement
              total_streams >= 2 AND
              completion_rate >= 0.5
    ),
    cohort_metrics AS (
        SELECT user_id,
            COUNT(*) AS shared_song_count,
            AVG(total_streams) AS avg_replays_on_shared_songs,
            AVG(completion_rate) AS avg_completion_on_shared_songs
        FROM cohort_with_shared_streamed_songs
        GROUP BY user_id
    ),
    cohort_normalized_metrics AS (
        SELECT user_id,
            shared_song_count AS "Shared Songs",
            avg_replays_on_shared_songs AS "Avg Replays",
            CAST(shared_song_count AS REAL) /
            (SELECT MAX(shared_song_count)
             FROM cohort_metrics) AS normalized_shared_songs,
            CAST(avg_replays_on_shared_songs AS REAL) /
            (SELECT MAX(avg_replays_on_shared_songs)
             FROM cohort_metrics) AS normalized_replays,
            avg_completion_on_shared_songs AS "Avg Completion"
        FROM cohort_metrics
    )
SELECT user_id,
       users.username AS Username,
       "Shared Songs",
       "Avg Replays",
       "Avg Completion",
       normalized_shared_songs,
       normalized_replays,
       (0.5 * normalized_shared_songs +
        0.3 * normalized_replays +
        0.2 * "Avg Completion") AS "Similarity Score"
FROM cohort_normalized_metrics cnm
JOIN users ON cnm.user_id = users.id
WHERE "Similarity Score" >= ?
ORDER BY "Similarity Score" DESC;
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- PERSONALIZED RECOMMENDATIONS (FIRST ATTEMPT - W/O WEIGHTED COLLABORATIVE FILTERING)
------------------------------------------------------------------------------------
-- GOAL:
-- Recommend songs to a user they have NOT streamed, based on similar users.

-- PROMPT:
-- Given a user_id, recommend songs liked by similar users
-- that the user has not streamed yet.

-- THOUGHT PROCESS:
-- * Find cohort of similar users based on the USER-TO-USER SIMILARITY query
-- * Find streams from the cohort that are above a certain level of engagement
-- * Exclude songs already streamed by the target user

-- QUERY:
WITH
    user_streamed_songs AS (
        SELECT song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id = ? AND
        -- Filter out streams with low engagement
              total_streams >= 2 AND
              completion_rate >= 0.5
    ),
    cohort_with_shared_streamed_songs AS (
        SELECT user_id, song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id != ? AND
              song_id IN (
                SELECT song_id
                FROM user_streamed_songs
              ) AND
              -- Filter out streams with low engagement
              total_streams >= 2 AND
              completion_rate >= 0.5
    ),
    similar_users AS (
        SELECT user_id,
               COUNT(*) AS shared_streamed_songs
        FROM cohort_with_shared_streamed_songs
        GROUP BY user_id
    ),
    similar_users_streams AS (
        SELECT song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id != ? AND
              user_id IN (
                SELECT user_id
                FROM similar_users
                ORDER BY shared_streamed_songs DESC
                LIMIT 5 -- Only reference the top 5 most similar users
              ) AND
              -- Filter out streams with low engagement
              total_streams >= 2 AND
              completion_rate >= 0.5
    ),
    similar_users_streams_metrics AS (
        SELECT song_id,
               COUNT(DISTINCT user_id) AS similar_users, -- number of similar users who streamed a song
               AVG(total_streams) AS avg_replays, -- avg replays of a song per user
               AVG(completion_rate) AS avg_completion_rate -- avg completion rate of a song per user
        FROM similar_users_streams
        GROUP BY song_id
    ),
    recommended_songs AS (
        SELECT song_id
        FROM similar_users_streams
        EXCEPT
        SELECT song_id
        FROM user_streamed_songs
    )
SELECT rs.song_id,
       songs.name AS song,
       artists.name AS artist,
       similar_users,
       avg_replays,
       avg_completion_rate
FROM recommended_songs rs
JOIN songs ON rs.song_id = songs.id
JOIN song_credits sc ON songs.id = sc.song_id
JOIN artists ON sc.artist_id = artists.id
JOIN similar_users_streams_metrics sm ON songs.id = sm.song_id
ORDER BY similar_users DESC,
         avg_replays DESC,
         avg_completion_rate DESC;
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- PERSONALIZED RECOMMENDATIONS (REFINED - WITH WEIGHTED COLLABORATIVE FILTERING)
------------------------------------------------------------------------------------
-- GOAL:
-- Recommend songs to a user they have NOT streamed, based on similar users.
-- Improve on previous query by implementing weighted collaborative filtering to
-- assign scores to recommended songs.

-- PROMPT:
-- Given a user_id, recommend songs liked by similar users
-- that the user has not streamed yet.

-- THOUGHT PROCESS:
-- * Find cohort of similar users based on the above USER-TO-USER SIMILARITY query
-- * Track similarity to target user by overlapping streams
-- * Find streams from the cohort
-- * Exclude songs already streamed by the target user
-- * Rank recommended songs by recommendation score.

-- QUERY:
WITH
    user_streamed_songs AS (
        SELECT song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id = ? AND
        -- Filter out streams with low engagement
              total_streams >= 2 AND
              completion_rate >= 0.5
    ),
    cohort_with_shared_streamed_songs AS (
        SELECT user_id, song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id != ? AND
              song_id IN (
                SELECT song_id
                FROM user_streamed_songs
              ) AND
              -- Filter out streams with low engagement
              total_streams >= 2 AND
              completion_rate >= 0.5
    ),
    similar_users AS (
        SELECT user_id,
               COUNT(*) AS overlap -- measures user's similarity strength
        FROM cohort_with_shared_streamed_songs
        GROUP BY user_id
),
    similar_users_streams AS (
        SELECT cm.user_id,
               cm.song_id,
               cm.total_streams,
               cm.completion_rate,
               su.overlap
        FROM candidate_metrics cm
        JOIN similar_users su ON cm.user_id = su.user_id
        WHERE cm.user_id != ? AND
              -- Filter out streams with low engagement
              total_streams >= 2 AND
              completion_rate >= 0.5
    ),
    similar_users_streams_metrics AS (
        SELECT song_id,
               COUNT(DISTINCT user_id) AS similar_users, -- number of similar users who streamed a song
               AVG(total_streams) AS avg_replays, -- avg replays per user of a song
               AVG(completion_rate) AS avg_completion_rate, -- avg completion rate per user of a song
               SUM(overlap) AS weighted_overlap -- total number of overlap points
        FROM similar_users_streams
        GROUP BY song_id
    ),
    normalized_metrics AS (
        SELECT song_id,
               similar_users,
               weighted_overlap,
               avg_replays,
               avg_completion_rate,
               CAST(similar_users AS REAL) / (
                    SELECT MAX(similar_users)
                    FROM similar_users_streams_metrics
               ) AS normalized_similar_users,
               CAST(avg_replays AS REAL) / (
                    SELECT MAX(avg_replays)
                    FROM similar_users_streams_metrics
               ) AS normalized_replays,
               CAST(weighted_overlap AS REAL) / (
                    SELECT MAX(weighted_overlap)
                    FROM similar_users_streams_metrics
               ) AS normalized_weighted_overlap
        FROM similar_users_streams_metrics
    ),
    recommended_songs AS (
        SELECT song_id
        FROM similar_users_streams
        EXCEPT
        SELECT song_id
        FROM user_streamed_songs
    )
SELECT rs.song_id,
       songs.name AS song,
       artists.name AS artist,
       similar_users,
       weighted_overlap,
       avg_replays,
       avg_completion_rate,
       (0.45 * normalized_weighted_overlap +
        0.25 * normalized_similar_users +
        0.20 * normalized_replays +
        0.10 * avg_completion_rate) AS recommendation_score
FROM recommended_songs rs
JOIN songs ON rs.song_id = songs.id
JOIN song_credits sc ON songs.id = sc.song_id
JOIN artists ON sc.artist_id = artists.id
JOIN normalized_metrics nm ON songs.id = nm.song_id
ORDER BY recommendation_score DESC;

-- NOTES:
-- * Weights were manually selected heuristically and could later be
-- tuned experimentally or learned from user interaction data.

-- SIMILAR_USERS VS WEIGHTED_OVERLAP:
-- * The similar_users metric captures BREADTH,
-- i.e., how many similar users streamed a song, where a similar user is someone who shares
-- at least one streamed song with the target user.
-- * The weighted_overlap metric captures STRENGTH,
-- i.e., how similar users are to the target user.

-- For example:
-- If User A overlaps with the target user on 18 songs, while
-- User B overlaps with the target user on 2 songs --
-- if both streamed Song X, User A influences the recommendation far more.
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- RECOMMENDATION EXPLANATION QUERIES
------------------------------------------------------------------------------------
-- 1. COLLABORATIVE EXPLANATION
-- GOAL:
-- For a given recommended song to a user, find:
-- * similar users who streamed the song
-- * their overlap scores
-- * avg replays
-- * avg completion

-- NOTE:
-- This is redundant.
-- These columns are already included in the recommended songs table.

-- QUERY
WITH
    user_streamed_songs AS ( -- target user's streamed songs
        SELECT song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id = ? AND -- the given user
        -- Filter out streams with low engagement
              total_streams >= 2 AND
              completion_rate >= 0.5
    ),
    cohort_with_shared_streamed_songs AS (
        SELECT user_id, song_id, total_streams, completion_rate
        FROM candidate_metrics
        WHERE user_id != ? AND -- exclude the given user
              song_id IN (
                SELECT song_id
                FROM user_streamed_songs
              ) AND
              -- Filter out streams with low engagement
              total_streams >= 2 AND
              completion_rate >= 0.5
    ),
    similar_users AS ( -- Users who share >= 1 stream w/ target user
        SELECT user_id,
               COUNT(*) AS overlap -- measures user's similarity strength
        FROM cohort_with_shared_streamed_songs
        GROUP BY user_id
    )
SELECT COUNT(DISTINCT cm.user_id) AS similar_users,
       SUM(su.overlap) AS weighted_overlap,
       AVG(cm.total_streams) AS avg_replays,
       AVG(cm.completion_rate) AS avg_completion_rate
FROM candidate_metrics cm
JOIN similar_users su ON cm.user_id = su.user_id
WHERE cm.song_id = ? -- the recommended song
      AND cm.total_streams >= 2
      AND cm.completion_rate >= 0.5;
      -- w/o engagement filters,
      -- low-engagement interactions w/ the recommended song affect
      -- explanation metrics, which creates inconsistency

-- 2. GENRE MATCH

-- QUERY:
SELECT genre
FROM user_genre_affinity
WHERE user_id = ?
ORDER BY affinity_score DESC
LIMIT 3;

-- 3. ARTIST MATCH

-- QUERY:
SELECT artist
FROM user_artist_affinity
WHERE user_id = ?
ORDER BY affinity_score DESC
LIMIT 3;

------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- GENRE AFFINITY SCORING
------------------------------------------------------------------------------------
-- GOAL:
-- Measure how strongly a user prefers each genre.

-- USEFUL METRICS:
-- Combine stream count, replay count, completion rate to assign scores
-- to each user's streamed genres.

-- THOUGHT PROCESS:
-- Given a user id:
-- * Find all genres streamed by the user
-- * Assign each streamed genre a score by the following system:

-- SCORING SYSTEM:
-- score = (stream_count weight) + (replay weight) + (completion weight)

-- TO COMPUTE:
-- For each genre streamed by a user:
-- * Find total streams, distinct songs, avg streams per song, avg completion rate
-- * Note: avg_streams_per_song = total streams per genre / distinct songs per genre

-- 1. Normalize metrics to similar ranges (i.e., between 0 and 1)
-- * normalized_streams = total_streams / max_total_streams
-- * normalized_replays = avg_streams_per_song / max_avg_streams_per_song
-- * avg_completion_rate is already naturally between 0 and 1

-- 2. score = 0.6 * normalized_streams + 0.2 * normalized_replays + 0.2 * avg_completion_rate

-- NOTE:
-- The candidate_metrics view already excludes skips and includes the following columns:
-- user_id, song_id, total_streams, total_ms_played, completion_rate, latest_stream

-- QUERY:
WITH
    user_streamed_genres AS (
        -- Note: each song currently corresponds to ONE genre,
        -- so the JOIN clause here is valid (i.e., each song maps to ONE genre)
        SELECT sg.genre_id,
               SUM(total_streams) AS total_streams,
               COUNT(DISTINCT cm.song_id) AS distinct_songs,
               AVG(completion_rate) AS avg_completion_rate,
               CAST(SUM(total_streams) AS REAL) / COUNT(DISTINCT cm.song_id) AS avg_streams_per_song
        FROM candidate_metrics cm
        JOIN song_genres sg ON cm.song_id = sg.song_id
        WHERE user_id = ?
        GROUP BY sg.genre_id
),
    normalized_metrics AS (
        SELECT genre_id,
               CAST(total_streams AS REAL) / (
                   SELECT MAX(total_streams)
                   FROM user_streamed_genres
               ) AS normalized_streams,
               CAST(avg_streams_per_song AS REAL) / (
                   SELECT MAX(avg_streams_per_song)
                   FROM user_streamed_genres
               ) AS normalized_replays,
               avg_completion_rate
        FROM user_streamed_genres
)
SELECT genre_id,
       genres.name AS genre,
       normalized_streams,
       normalized_replays,
       avg_completion_rate,
       (0.6 * normalized_streams +
        0.2 * normalized_replays +
        0.2 * avg_completion_rate) AS affinity_score
FROM normalized_metrics nm
JOIN genres ON nm.genre_id = genres.id
ORDER BY affinity_score DESC;
------------------------------------------------------------------------------------
------------------------------------------------------------------------------------
-- ARTIST AFFINITY SCORING
------------------------------------------------------------------------------------
-- GOAL:
-- Measure how strongly a user prefers each artist.

-- USEFUL METRICS:
-- Combine stream count, replay count, completion rate to assign scores
-- to each user's streamed artists.

-- THOUGHT PROCESS:
-- Given a user id:
-- * Find all artists streamed by the user
-- * Assign each streamed artist a score by the following system:

-- SCORING SYSTEM:
-- score = (stream_count weight) + (replay weight) + (completion weight)

-- TO COMPUTE:
-- For each artist streamed by a user:
-- * Find total streams, distinct songs, avg streams per song, avg completion rate
-- * Note: avg_streams_per_song = total streams per artist / distinct songs per artist

-- 1. Normalize metrics to similar ranges (i.e., between 0 and 1)
-- * normalized_streams = total_streams / max_total_streams
-- * normalized_replays = avg_streams_per_song / max_avg_streams_per_song
-- * avg_completion_rate is already naturally between 0 and 1

-- 2. score = 0.6 * normalized_streams + 0.2 * normalized_replays + 0.2 * avg_completion_rate

-- QUERY:
WITH
    user_streamed_artists AS (
        -- Note: each song currently corresponds to ONE artist,
        -- so the JOIN clause here is valid (i.e., each song maps to ONE artist)
        SELECT sc.artist_id,
               SUM(total_streams) AS total_streams,
               COUNT(DISTINCT cm.song_id) AS distinct_songs,
               AVG(completion_rate) AS avg_completion_rate,
               CAST(SUM(total_streams) AS REAL) / COUNT(DISTINCT cm.song_id) AS avg_streams_per_song
        FROM candidate_metrics cm
        JOIN song_credits sc ON cm.song_id = sc.song_id
        WHERE user_id = ?
        GROUP BY sc.artist_id
),
    normalized_metrics AS (
        SELECT artist_id,
               CAST(total_streams AS REAL) / (
                   SELECT MAX(total_streams)
                   FROM user_streamed_artists
               ) AS normalized_streams,
               CAST(avg_streams_per_song AS REAL) / (
                   SELECT MAX(avg_streams_per_song)
                   FROM user_streamed_artists
               ) AS normalized_replays,
               avg_completion_rate
        FROM user_streamed_artists
)
SELECT artist_id,
       artists.name AS artist,
       normalized_streams,
       normalized_replays,
       avg_completion_rate,
       (0.6 * normalized_streams +
        0.2 * normalized_replays +
        0.2 * avg_completion_rate) AS affinity_score
FROM normalized_metrics nm
JOIN artists ON nm.artist_id = artists.id
ORDER BY affinity_score DESC;
------------------------------------------------------------------------------------
