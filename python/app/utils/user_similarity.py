import sqlite3
import pandas as pd
from utils import DB_PATH


# DB_PATH = "/workspaces/music-streaming-project/db/music.db"

# Expects a user_id
# Returns a dataframe of similar users with columns:
# "user_id","Username", "Shared Songs", "Avg Replays",
# "Avg Completion", "normalized_shared_songs", "normalized_replays",
# "Similarity Score"
def get_similar_users(user_id: int,
                      min_score: float = 0.25,
                      db_path: str = DB_PATH) -> pd.DataFrame:
    query = """
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
                ROUND("Avg Replays", 1) AS "Avg Replays",
                ROUND("Avg Completion", 2) AS "Avg Completion",
                normalized_shared_songs,
                normalized_replays,
                ROUND((0.5 * normalized_shared_songs +
                    0.3 * normalized_replays +
                    0.2 * "Avg Completion"), 2) AS "Similarity Score"
            FROM cohort_normalized_metrics cnm
            JOIN users ON cnm.user_id = users.id
            WHERE "Similarity Score" >= ?
            ORDER BY "Similarity Score" DESC;
            """

    with sqlite3.connect(db_path) as con:

        df = pd.read_sql_query(query, con,
                               params=(user_id, user_id, min_score))

    return df
