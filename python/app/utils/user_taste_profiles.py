import sqlite3

DB_PATH = "/workspaces/music-streaming-project/db/music.db"

DAY = [8,9,10,11,12,13,14,15,16,17]
NIGHT = [20,21,22,23,0,1,2]

# Runs several SQL queries
# Returns a user's behavior metrics as a dict containing
# avg_completion_rate, skip_rate, avg_streams_per_song, distinct_songs
# hour_shares, dominant_genre_share, diversity score
def get_user_behavior_metrics(user_id: int, db_path: str = DB_PATH) -> dict:

    with sqlite3.connect(db_path) as con:

        cur = con.cursor()

        # Get avg_completion_rate, skip_rate, avg_streams_per_song, distinct_songs
        # from user_behavior_metrics

        query = """
                SELECT avg_completion_rate,
                       skip_rate,
                       avg_streams_per_song,
                       distinct_songs
                FROM user_behavior_metrics
                WHERE user_id = ?
                """

        cur.execute(query, (user_id,))

        stats = cur.fetchone()

        behavior_metrics = {
            "user_id": user_id,
            "avg_completion_rate": stats[0],
            "skip_rate": stats[1],
            "avg_streams_per_song": stats[2],
            "distinct_songs": stats[3]
        }

        # Get hour, hour_share from user_listening_hours

        query = """
                SELECT hour, hour_share
                FROM user_listening_hours
                WHERE user_id = ?
                """

        cur.execute(query, (user_id,))

        hours = cur.fetchall()

        hour_shares = []

        for hour in hours:
            hour_shares.append({"hour": int(hour[0]),
                                "hour_share": hour[1]})

        behavior_metrics["hour_shares"] = hour_shares

        # Get dominant_genre_share diversity_score from user_diversity_metrics

        query = """
                SELECT dominant_genre_share, diversity_score
                FROM user_diversity_metrics
                WHERE user_id = ?
                """

        cur.execute(query, (user_id,))

        stats = cur.fetchone()

        behavior_metrics["dominant_genre_share"] = stats[0]
        behavior_metrics["diversity_score"] = stats[1]

        return behavior_metrics


# Expects a user's behavior metrics as the dictionary
# returned by get_user_behavior_metrics
# Returns a list of listener types for the user
def classify_listener_type(user_behavior_metrics: dict) -> list:

    ubm = user_behavior_metrics

    hour_shares = ubm["hour_shares"]

    listener_types = []

    # FOCUSED LISTENER:
    # low diversity + high replay behavior, i.e.,
    # user repeatedly listens to a smaller set of music
    if ubm["diversity_score"] <= 0.5 and ubm["avg_streams_per_song"] >= 2.5:
       listener_types.append("Focused Listener")

    # EXPLORER:
    # high diversity + many distinct songs, i.e.,
    # user samples broadly across genres/artists
    if ubm["diversity_score"] > 0.75 and ubm["distinct_songs"] > 50:
        listener_types.append("Explorer")

    # COMPLETION-ORIENTED LISTENER:
    # rarely skips and fully listens
    if ubm["skip_rate"] <= 0.15 and ubm["avg_completion_rate"] >= 0.8:
        listener_types.append("Completion-Oriented Listener")

    # CASUAL SKIPPER:
    # high skip behavior
    if ubm["skip_rate"] > 0.4:
        listener_types.append("Casual Skipper")

    # REPLAY-HEAVY LISTENER:
    # very high replay tendency
    if ubm["avg_streams_per_song"] >= 3:
        listener_types.append("Replay-Heavy Listener")

    # NIGHT LISTENER:
    # majority listening concentrated late
    night_share = 0
    for hour in hour_shares:
        if hour["hour"] in NIGHT:
            night_share += hour["hour_share"]

    if night_share > 0.5:
        listener_types.append("Night Listener")

    # DAY LISTENER:
    # majority listening concentrated early
    day_share = 0
    for hour in hour_shares:
        if hour["hour"] in DAY:
            day_share += hour["hour_share"]

    if day_share > 0.5:
        listener_types.append("Day Listener")

    # GENRE LOYALIST:
    # one genre dominates listening
    if ubm["dominant_genre_share"] > 0.65:
        listener_types.append("Genre Loyalist")

    # BALANCED LISTENER:
    # moderate diversity + low skip rate
    if 0.45 <= ubm["diversity_score"] <= 0.75 and ubm["skip_rate"] < 0.25:
        listener_types.append("Balanced Listener")

    return listener_types


# Runs several SQL queries
# Assembles the result
# Returns one structured profile as a dict containing:
# user_id, top_genres, top_artists, behavior, listening_hours
def get_user_taste_profile(user_id: int, db_path: str = DB_PATH) -> dict:

    profile = {"user_id": user_id}

    with sqlite3.connect(db_path) as con:

        cur = con.cursor()

        # TOP GENRES: Get user's top 3 genres and their affinity scores

        query = """
                SELECT genre, affinity_score
                FROM user_genre_affinity
                WHERE user_id = ?
                ORDER BY affinity_score DESC
                LIMIT 3
                 """

        cur.execute(query, (user_id,))

        top_genres = cur.fetchall()

        genres = []

        for genre in top_genres:
            genres.append({"genre": genre[0],
                           "score": genre[1]})

        profile["top_genres"] = genres

        # TOP_ARTISTS: Get user's top 3 artists and their affinity_scores

        query = """
                SELECT artist, affinity_score
                FROM user_artist_affinity
                WHERE user_id = ?
                ORDER BY affinity_score DESC
                LIMIT 3
                 """

        cur.execute(query, (user_id,))

        top_artists = cur.fetchall()

        artists = []

        for artist in top_artists:
            artists.append({"artist": artist[0],
                            "score": artist[1]})

        profile["top_artists"] = artists

        # BEHAVIOR: Get user's avg_completion_rate, skip_rate, diversity_score, and peak hours

        query = """
                SELECT avg_completion_rate, skip_rate
                FROM user_behavior_metrics
                WHERE user_id = ?
                 """

        cur.execute(query, (user_id,))

        rates = cur.fetchone()

        behavior = {"avg_completion_rate": rates[0],
                    "skip_rate": rates[1]}

        query = """
                SELECT diversity_score
                FROM user_diversity_metrics
                WHERE user_id = ?
                 """

        cur.execute(query, (user_id,))

        diversity_score = cur.fetchall()

        behavior["diversity_score"] = diversity_score[0][0]

        query = """
                SELECT hour
                FROM user_listening_hours
                WHERE user_id = ?
                ORDER BY total_streams DESC
                LIMIT 3
                 """

        cur.execute(query, (user_id,))

        top_hours = cur.fetchall()

        peak_hours = []

        for hour in top_hours:
            peak_hours.append(hour[0])

        behavior["peak_hours"] = peak_hours

        profile["behavior"] = behavior

        # Get behavior metrics to classify listener type

        behavior_metrics = get_user_behavior_metrics(user_id=user_id)

        profile["listener_types"] = classify_listener_type(behavior_metrics)

        return profile


if __name__ == "__main__":
    profile = get_user_taste_profile(user_id=29)
    for _ in profile:
        print(f"{_}: {profile[_]}")
    # profile = get_user_behavior_metrics(user_id=29)
    # for _ in profile:
    #     print(f"{_}: {profile[_]}")

