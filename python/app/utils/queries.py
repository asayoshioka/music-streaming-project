import sqlite3
import pandas as pd
from utils import DB_PATH


# DB_PATH = "/workspaces/music-streaming-project/db/music.db"

# Return total listening hours
def get_total_listening_hours(db_path: str = DB_PATH) -> float:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute("""
                    SELECT CAST(SUM(ms_played) AS REAL) /
                               (1000 * 3600)
                    FROM streams
                    """)
        return round(cur.fetchone()[0],2)


# Return dataframe with "Country" and "Users" columns:
def get_country_counts(db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        query = """
                SELECT country AS Country,
                       COUNT(*) AS Users
                FROM users
                GROUP BY Country;
                """
        df = pd.read_sql_query(query, con)
        return df


# Return dataframe with "Genre" and "Total Streams" columns:
def get_top_genres(limit: int = 5, db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        query = f"""
                SELECT genres.name AS Genre,
                       COUNT(*) AS "Total_Streams"
                FROM streams
                JOIN song_genres ON song_genres.song_id = streams.song_id
                JOIN genres ON genres.id = song_genres.genre_id
                GROUP BY genres.id
                ORDER BY "Total_Streams" DESC
                LIMIT {limit};
                """
        df = pd.read_sql_query(query, con)
        return df


# Return dataframe with "Song", "Artist", and "Total Streams" columns:
def get_top_songs(limit: int = 5, db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        query = f"""
                WITH top_songs AS (
                    SELECT song_id, COUNT(*) AS total_streams
                    FROM streams
                    GROUP BY song_id
                )
                SELECT s.name AS Song,
                       a.name AS Artist,
                       ts.total_streams AS "Total Streams"
                FROM top_songs ts
                JOIN songs s ON ts.song_id=s.id
                JOIN song_credits sc ON s.id=sc.song_id
                JOIN artists a ON sc.artist_id = a.id
                ORDER BY "Total Streams" DESC
                LIMIT {limit};
                 """
        df = pd.read_sql_query(query, con)
        return df


# Return dataframe with "Artist" and "Total Streams" columns:
def get_top_artists(limit: int = 5, db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        query = f"""
                SELECT a.name AS Artist,
                       COUNT(*) AS "Total Streams"
                FROM streams s
                JOIN song_credits sc ON s.song_id = sc.song_id
                JOIN artists a ON sc.artist_id = a.id
                GROUP BY a.id
                ORDER BY "Total Streams" DESC
                LIMIT {limit};
                """
        df = pd.read_sql_query(query, con)
        return df


# Returns dataframe with "Song" and "Avg Replays" columns:
def get_top_replayed_songs(limit: int = 5, db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        query = f"""
                WITH top_replayed_songs AS (
                    SELECT song_id,
                           ROUND(AVG(total_streams), 1) AS "Avg Replays"
                    FROM candidate_metrics
                    GROUP BY song_id
                    ORDER BY "Avg Replays" DESC
                    LIMIT {limit}
                )
                SELECT s.name AS Song,
                       a.name AS Artist,
                       "Avg Replays"
                FROM top_replayed_songs trs
                JOIN song_credits sc ON trs.song_id = sc.song_id
                JOIN songs s ON sc.song_id = s.id
                JOIN artists a ON sc.artist_id = a.id
                ORDER BY "Avg Replays" DESC
                 """
        df = pd.read_sql_query(query, con)
        return df


# Returns dataframe with "Genre" and "Genre Share" columns
def get_genre_shares(db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        query = """
                SELECT genres.name AS "Genre",
                       CAST(COUNT(*) AS REAL) / (
                           SELECT COUNT(*)
                           FROM streams) AS "Genre Share"
                FROM streams
                JOIN song_genres sg ON streams.song_id = sg.song_id
                JOIN genres ON sg.genre_id = genres.id
                GROUP BY sg.genre_id;
                """
        df = pd.read_sql_query(query, con)
        return df


# Returns a tuple of user's top 3 genres
def get_user_top_genres(user_id: int, db_path: str = DB_PATH) -> tuple:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = f"""
                SELECT genre
                FROM user_genre_affinity
                WHERE user_id = {user_id}
                ORDER BY affinity_score DESC
                LIMIT 3;
                """
        cur.execute(query)
        return tuple(row[0] for row in cur.fetchall())


# Returns a tuple of user's top 3 artists
def get_user_top_artists(user_id: int, db_path: str = DB_PATH) -> tuple:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = f"""
                SELECT artist
                FROM user_artist_affinity
                WHERE user_id = {user_id}
                ORDER BY affinity_score DESC
                LIMIT 3;
                """
        cur.execute(query)
        return tuple(row[0] for row in cur.fetchall())


# Returns a song's genre given its song_id
def get_song_genre(song_id: int, db_path: str = DB_PATH) -> str:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(f"""
            SELECT g.name
            FROM song_genres sg
            JOIN genres g ON sg.genre_id = g.id
            WHERE sg.song_id = {song_id}
                     """)
        return cur.fetchone()[0]


# Return dataframe with the following columns:
# "Hour of Day", "Total Streams", "Avg Hour Share", "Avg Completion Rate", "Avg Skip Rate"
def get_hour_analytics(db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = """SELECT hour AS "Hour of Day",
                          SUM(total_streams) AS "Total Streams",
                          AVG(hour_share) AS "Avg Hour Share",
                          AVG(avg_completion_rate) AS "Avg Completion Rate",
                          AVG(skip_rate) AS "Avg Skip Rate"
                   FROM user_listening_hours
                   GROUP BY hour
                   ORDER BY hour;
                """
        df = pd.read_sql_query(query, con)
        return df


# Return dataframe with the following columns:
# "Skip Rate", "Avg Completion Rate", "Avg Streams Per Song"
# "Distinct Genres", "Distinct Artists"
def get_behavior_data(db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = """SELECT skip_rate AS "Skip Rate",
                          avg_completion_rate AS "Avg Completion Rate",
                          avg_streams_per_song AS "Avg Streams Per Song",
                          distinct_genres AS "Distinct Genres",
                          distinct_artists AS "Distinct Artists"
                   FROM user_behavior_metrics
                """
        df = pd.read_sql_query(query, con)
        return df


# Return a one column dataframe with all user's diversity_scores
def get_diversity_scores(db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = """SELECT diversity_score AS "Diversity Score"
                   FROM user_diversity_metrics;
                """
        df = pd.read_sql_query(query, con)
        return df


# Returns a tuple of all songs in the database
def get_song_titles_and_artists(db_path: str = DB_PATH) -> tuple:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = """SELECT songs.name,
                          artists.name
                   FROM songs
                   JOIN song_credits sc ON songs.id = sc.song_id
                   JOIN artists on sc.artist_id = artists.id
                   ORDER BY songs.name ASC
                """
        cur.execute(query)
        return tuple(f"\"{row[0]}\" by {row[1]}" for row in cur.fetchall())


# Returns the number of rows of a specified table
def count_rows(table: str, db_path: str = DB_PATH) -> int:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        return cur.fetchone()[0]


# Expects two user ids
# Returns shared streamed songs with
# total_streams >= 2 and completion_rate >= 0.5
def get_shared_songs(user_1: int, user_2: int, db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:

        query = """
                SELECT cm.song_id,
                       s.name AS Song,
                       a.name AS Artist,
                       AVG(cm.total_streams) AS "Avg Replays",
                       AVG(cm.completion_rate) AS "Avg Completion"
                FROM candidate_metrics cm
                JOIN songs s ON cm.song_id = s.id
                JOIN song_credits sc ON s.id = sc.song_id
                JOIN artists a ON sc.artist_id = a.id
                WHERE cm.user_id IN (?, ?) AND
                      cm.total_streams >= 2 AND
                      cm.completion_rate >= 0.5
                GROUP BY cm.song_id
                HAVING COUNT(DISTINCT cm.user_id) = 2
                ORDER BY "Avg Replays" DESC
                """

        df = pd.read_sql_query(query, con, params=(user_1, user_2))

        return df


# Expects a list of user_ids.
# Returns a dataframe with "hour", "avg_hour_share" columns
# for the given user_ids.
def get_avg_hour_shares(user_ids: list, db_path: str = DB_PATH) -> pd.DataFrame:

    # Create a comma-separated string of "?" placeholders
    placeholders = ",".join(["?"] * len(user_ids))

    query = f"""
            SELECT hour AS "Hour of Day",
                   AVG(hour_share) As "Avg Hour Share"
            FROM user_listening_hours
            WHERE user_id IN ({placeholders})
            GROUP BY hour
            ORDER BY hour ASC
            """

    with sqlite3.connect(db_path) as con:

        df = pd.read_sql_query(query, con, params=user_ids)

    return df


# Expects a list of given users
# Returns their average diversity score
def get_avg_diversity_score(user_ids: list = None, db_path: str = DB_PATH) -> float:

    # Create a comma-separated string of "?" placeholders
    placeholders = ",".join(["?"] * len(user_ids))
    query = f"""
            SELECT ROUND(AVG(diversity_score), 2) As "Avg Diversity Score"
            FROM user_diversity_metrics
            WHERE user_id IN ({placeholders})
            """

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(query, user_ids)
        return cur.fetchone()[0]


# Expects a list of given users
# Returns their average distinct songs
def get_avg_distinct_songs(user_ids: list = None, db_path: str = DB_PATH) -> float:

    # Create a comma-separated string of "?" placeholders
    placeholders = ",".join(["?"] * len(user_ids))
    query = f"""
            SELECT ROUND(AVG(distinct_songs), 1) As "Avg Distinct Songs"
            FROM user_behavior_metrics
            WHERE user_id IN ({placeholders})
              """

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(query, user_ids)
        return cur.fetchone()[0]


# Expects a list of given users
# Returns their average skip rate
def get_avg_skip_rate(user_ids: list = None, db_path: str = DB_PATH) -> float:

    # Create a comma-separated string of "?" placeholders
    placeholders = ",".join(["?"] * len(user_ids))
    query = f"""
            SELECT ROUND(AVG(skip_rate), 2) As "Avg Skip Rate"
            FROM user_behavior_metrics
            WHERE user_id IN ({placeholders})
              """

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(query, user_ids)
        return cur.fetchone()[0]


# Expects a list of given users
# Returns their average dominant genre share
def get_avg_dom_genre_share(user_ids: list = None, db_path: str = DB_PATH) -> float:

    # Create a comma-separated string of "?" placeholders
    placeholders = ",".join(["?"] * len(user_ids))
    query = f"""
            SELECT ROUND(AVG(dominant_genre_share), 2) As "Avg Dominant Genre Share"
            FROM user_diversity_metrics
            WHERE user_id IN ({placeholders})
              """

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(query, user_ids)
        return cur.fetchone()[0]


# Expects a list of given users
# Returns their average streams per song
def get_avg_streams_per_song(user_ids: list = None, db_path: str = DB_PATH) -> float:

    # Create a comma-separated string of "?" placeholders
    placeholders = ",".join(["?"] * len(user_ids))
    query = f"""
            SELECT ROUND(AVG(avg_streams_per_song), 2) As "Avg Streams Per Song"
            FROM user_behavior_metrics
            WHERE user_id IN ({placeholders})
              """

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(query, user_ids)
        return cur.fetchone()[0]


# Expects a list of given users
# Returns their average completion rate
def get_avg_completion_rate(user_ids: list = None, db_path: str = DB_PATH) -> float:

    # Create a comma-separated string of "?" placeholders
    placeholders = ",".join(["?"] * len(user_ids))
    query = f"""
            SELECT ROUND(AVG(avg_completion_rate), 2) As "Avg Completion Rate"
            FROM user_behavior_metrics
            WHERE user_id IN ({placeholders})
              """

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(query, user_ids)
        return cur.fetchone()[0]


# Returns a df with the following columns:
# "user_id", "skip_rate", "avg_streams_per_song", "avg_completion_rate",
# "diversity_score", "dominant_genre_share"
def get_behavior_df(db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = """SELECT ubm.user_id,
                          ubm.skip_rate AS "Skip Rate",
                          ubm.avg_streams_per_song AS "Avg Streams Per Song",
                          ubm.avg_completion_rate AS "Avg Completion Rate",
                          udm.diversity_score AS "Diversity Score",
                          udm.dominant_genre_share AS "Dominant Genre Share"
                   FROM user_behavior_metrics ubm
                   JOIN user_diversity_metrics udm ON ubm.user_id = udm.user_id
                """
        df = pd.read_sql_query(query, con)
        return df


def get_liked_songs(user_id: int, db_path: str = DB_PATH) -> pd.DataFrame:

    query = """
            SELECT songs.name AS Song,
                   artists.name AS Artist,
                   liked_datetime AS "Liked On"
            FROM liked_songs ls
            JOIN songs ON ls.song_id = songs.id
            JOIN song_credits sc ON songs.id = sc.song_id
            JOIN artists ON sc.artist_id = artists.id
            WHERE ls.user_id = ?
            ORDER BY liked_datetime DESC
            """

    with sqlite3.connect(db_path) as con:

        return pd.read_sql_query(query, con, params=(user_id,))


def get_similar_user_count(user_id: int, db_path: str = DB_PATH) -> int:

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
        )
    SELECT COUNT(DISTINCT user_id)
    FROM cohort_with_shared_streamed_songs;
            """

    with sqlite3.connect(DB_PATH) as con:

        return pd.read_sql_query(query, con).iloc[0,0]


# Returns user_behavior_metrics view as a dataframe
def get_user_behavior_metrics(db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        return pd.read_sql_query("SELECT * FROM user_behavior_metrics", con)


# Returns user_diversity_metrics view as a dataframe
def get_user_diversity_metrics(db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        return pd.read_sql_query("SELECT * FROM user_diversity_metrics", con)

# Returns users table as a dataframe
def get_users(db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        return pd.read_sql_query("SELECT * FROM users", con)


# Returns dataframe with "year_month" and "streams" columns
def get_streams_by_month(db_path: str = DB_PATH) -> pd.DataFrame:

    query = """
            SELECT
                STRFTIME('%Y-%m', start_datetime) AS year_month,
                COUNT(*) AS total_streams
            FROM
                streams
            GROUP BY
                year_month
            ORDER BY
                year_month ASC
            """

    with sqlite3.connect(db_path) as con:
        return pd.read_sql_query(query, con)


def get_user_total_streams(user_id: int, db_path: str = DB_PATH) -> int:

    query = """
            SELECT COUNT(*)
            FROM streams
            WHERE user_id = ?
            """

    with sqlite3.connect(db_path) as con:

        cur = con.cursor()
        cur.execute(query, (user_id,))

        return cur.fetchone()[0]


def get_user_signup(user_id: int, db_path: str = DB_PATH) -> str:

    query = """
            SELECT signup_date
            FROM users
            WHERE id = ?
            """

    with sqlite3.connect(db_path) as con:

        cur = con.cursor()
        cur.execute(query, (user_id,))

        return cur.fetchone()[0]


def get_user_listening_hours(db_path: str = DB_PATH) -> pd.DataFrame:

    with sqlite3.connect(db_path) as con:
        query = "SELECT * FROM user_listening_hours"
        return pd.read_sql_query(query, con)


def get_song_stats(song_id: int, db_path: str = DB_PATH) -> pd.DataFrame:

    query  = """
             SELECT COUNT(*) AS total_listeners,
                    AVG(total_streams) AS avg_replays,
                    AVG(completion_rate) AS avg_completion
             FROM candidate_metrics
             WHERE song_id = ?
             """
    with sqlite3.connect(db_path) as con:
        return pd.read_sql_query(query, con, params=(song_id,))

if __name__ == "__main__":
    print(get_user_top_artists(1))
    print(get_user_top_genres(1))
    print(get_song_genre(1))


