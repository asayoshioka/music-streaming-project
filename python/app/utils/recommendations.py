import sqlite3
import pandas as pd
import textwrap
from utils.queries import (get_user_top_genres,
                     get_user_top_artists,
                     get_song_genre)
from utils.get_ids_and_maps import get_id_value_map

DB_PATH = "/workspaces/273640407/music_db_project/db/music.db"

SONG_MAP = get_id_value_map(table="songs", value_column="name")

# ** FOR RECOMMENDATIONS GIVEN A USER **

# Returns Recommended Songs df for a given user id
# w/ the following columns:
# song_id, Song, Artist, Rec Score, Overlap Strength,
# Overlap Breadth,Avg Replays, Avg Completion
def get_recommendations_for_user(user_id: int,
                        min_score: float = 0.25,
                        max_recs: int = 15,
                        db_path: str = DB_PATH) -> pd.DataFrame:

    # PERSONALIZED RECOMMENDATION QUERY
    query = f"""
    WITH
        user_streamed_songs AS (
            SELECT song_id, total_streams, completion_rate
            FROM candidate_metrics
            WHERE user_id = {user_id} AND
            -- Filter out streams with low engagement
                total_streams >= 2 AND
                completion_rate >= 0.5
        ),
        cohort_with_shared_streamed_songs AS (
            SELECT user_id, song_id, total_streams, completion_rate
            FROM candidate_metrics
            WHERE user_id != {user_id} AND
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
            WHERE cm.user_id != {user_id} AND
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
    SELECT  rs.song_id,
            songs.name AS Song,
            artists.name AS Artist,
            ROUND(
            (0.45 * normalized_weighted_overlap +
            0.25 * normalized_similar_users +
            0.20 * normalized_replays +
            0.10 * avg_completion_rate), 2) AS "Rec Score",
        weighted_overlap AS "Overlap Strength",
        similar_users AS "Overlap Breadth",
        ROUND(avg_replays, 1) AS "Avg Replays",
        avg_completion_rate AS "Avg Completion",
        normalized_weighted_overlap,
        normalized_similar_users,
        normalized_replays
    FROM recommended_songs rs
    JOIN songs ON rs.song_id = songs.id
    JOIN song_credits sc ON songs.id = sc.song_id
    JOIN artists ON sc.artist_id = artists.id
    JOIN normalized_metrics nm ON songs.id = nm.song_id
    WHERE "Rec Score" >= {min_score}
    ORDER BY "Rec Score" DESC
    LIMIT {max_recs};
            """

    with sqlite3.connect(db_path) as con:

        # Construct a personalized rec. dataframe
        df = pd.read_sql_query(query, con)

        return df


# Expects a user_id, song title, and
# the song recommendation dataframe returned by get_recommendations.
# Returns structured song recommendation data as a dict.
# of the form:
# {
#  "song": ...,
#  "artist": ...,
#  "recommendation_score": ...,
#  "because": {"weighted_overlap": ...,
#              "similar_users": ...,
#              "avg_replays": ...,
#              "avg_completion_rate": ...,
#              "matching_top_genre": ...,
#              "matching_top_artist": ...
#               }
# }
def get_recommendation_profile(user_id: int,
                               song: str,
                               df: pd.DataFrame) -> dict:

    # Get song row from the song rec dataframe
    row = tuple(df.loc[df["Song"] == song].iloc[0])

    song_id = row[0]

    rec_profile = {
        "song": {song},
        "artist": row[2],
        "recommendation_score": row[3],
        "because": {
            "weighted_overlap": row[4],
            "similar_users": row[5],
            "avg_replays": row[6],
            "avg_completion_rate": row[7]
        }
    }

    # Get user's top genres and artists
    top_genres = get_user_top_genres(user_id=user_id)
    top_artists = get_user_top_artists(user_id=user_id)

    # Get song's genre
    song_genre = get_song_genre(song_id)

    if row[2] in top_artists:
        rec_profile["because"]["matching_top_artist"] = row[2]

    if song_genre in top_genres:
        rec_profile["because"]["matching_top_genre"] = song_genre

    return rec_profile


# Expects the recommendation profile dictionary
# returned by get_recommendation_profile
# Returns a recommendation explanation str
def explain_recommendation(rec_profile: dict) -> str:

    rec_score = rec_profile["recommendation_score"]

    similar_users = rec_profile["because"]["similar_users"]

    avg_replays = rec_profile["because"]["avg_replays"]

    avg_completion_rate = rec_profile["because"]["avg_completion_rate"]

    artist = rec_profile["artist"]

    explanation = textwrap.dedent(f"""
        :grey[Recommendation score] &nbsp; **:green[{rec_score:.2f}]**

        :green[:material/Group:] &nbsp; Recommended because :green-badge[{similar_users} similar users]
        streamed this song frequently.

        :violet[:material/Repeat:] &nbsp; Listeners similar to you replay this song an average of
        :green-badge[{avg_replays:.1f}&times;] with a completion rate of :green-badge[{avg_completion_rate:.0%}].
        """)

    if "matching_top_genre" in rec_profile["because"]:

        genre = rec_profile["because"]["matching_top_genre"]

        explanation += f"\n\n:red[:material/Favorite:] &nbsp; Aligns with your strong preference for :green-badge[{genre}]."

    if "matching_top_artist" in rec_profile["because"]:

        explanation += f"\n\n:blue[:material/Music_Note:] &nbsp; You frequently listen to :green-badge[{artist}]."

    return explanation


# ** FOR RECOMMENDATIONS GIVEN A SONG **


# Returns Recommended Songs df for a given song id
def get_recommendations_for_song(song_id: int,
                                min_score: float = 0.25,
                                limit: int = 15,
                                db_path = DB_PATH) -> pd.DataFrame:

    query = f"""
            WITH
                cohort_who_streamed_song AS (
                    SELECT user_id
                    FROM candidate_metrics
                    WHERE song_id = {song_id}
            ),
                cohort_other_streamed_songs AS (
                    SELECT song_id, total_streams, completion_rate
                    FROM candidate_metrics
                    WHERE user_id IN (
                        SELECT user_id
                        FROM cohort_who_streamed_song
                    )
                    -- Exclude the original shared streamed song
                    AND song_id != {song_id}
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
                songs.name AS Song,
                artists.name AS Artist,
                ROUND((0.6 * normalized_shared +
                0.2 * normalized_replays +
                0.2 * avg_completion_rate), 2) AS "Rec Score",
                shared_users AS "Shared Users",
                avg_streams_per_user AS "Avg Replays",
                avg_completion_rate AS "Avg Completion",
                normalized_shared,
                normalized_replays
            FROM normalized_metrics nm
            JOIN songs ON nm.song_id = songs.id
            JOIN song_credits sc ON songs.id=sc.song_id
            JOIN artists ON sc.artist_id=artists.id
            WHERE "Rec Score" >= {min_score}
            ORDER BY "Rec Score" DESC
            LIMIT {limit};
             """

    with sqlite3.connect(db_path) as con:

        df = pd.read_sql_query(query, con)
        return df


# song1 is the selected song's id as an int.
# song2 is the recommended song's title as a str.
# df is the recommended songs dataframe returned by
# get_recommendations_for_song.
# Returns structured song recommendation data as a dict.
# of the form:
# {
#  "song": ...,
#  "artist": ...,
#  "recommendation_score": ...,
#  "because": {"shared_users": ...,
#              "avg_replays": ...,
#              "avg_completion_rate": ...,
#              "matching_genre": ...
#               }
# }
def get_recommendation_profile_2(song1_id: int,
                                 song2: str,
                                 df: pd.DataFrame) -> dict:

    # Get song row from the song rec dataframe
    row = tuple(df.loc[df["Song"] == song2].iloc[0])

    song2_id = row[0]

    rec_profile = {
        "target_song_id" : song1_id,
        "rec_song": song2,
        "artist": row[2],
        "recommendation_score": row[3],
        "because": {
            "shared_users": row[4],
            "avg_replays": row[5],
            "avg_completion_rate": row[6]
        }
    }

    # Get song 1's genre
    song1_genre = get_song_genre(song1_id)

    # Get song 2's genre
    song2_genre = get_song_genre(song2_id)

    if song1_genre == song2_genre:
        rec_profile["because"]["matching_genre"] = song1_genre

    return rec_profile


# Expects the recommendation profile dictionary
# returned by get_recommendation_profile2
# Returns a recommendation explanation str
def explain_recommendation_2(rec_profile: dict) -> str:

    target_song = SONG_MAP[rec_profile["target_song_id"]]

    rec_score = rec_profile["recommendation_score"]

    shared_users = rec_profile["because"]["shared_users"]

    avg_replays = rec_profile["because"]["avg_replays"]

    avg_completion_rate = rec_profile["because"]["avg_completion_rate"]

    artist = rec_profile["artist"]

    explanation = textwrap.dedent(f"""
        :grey[Recommendation Score: **:green[{rec_score:.2f}]**]

        :green[:material/Group:] &nbsp; Recommended because :green-badge[{shared_users} users] who streamed
        {target_song} also streamed this one.

        :violet[:material/Repeat:] &nbsp; These listeners replayed it an average of
        :green-badge[{avg_replays:.1f}] times
        with a completion rate of :green-badge[{avg_completion_rate:.0%}].
        """)

    if "matching_genre" in rec_profile["because"]:

        genre = rec_profile["because"]["matching_genre"]

        explanation += f"\n\n:blue[:material/Music_Note:] &nbsp; Both songs share the same genre: :green-badge[{genre}]."

    return explanation

if __name__ == "__main__":
    ...
