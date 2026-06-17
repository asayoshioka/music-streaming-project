import sqlite3
import random

random.seed(42)

DB_PATH = "/workspaces/273640407/music_db_project/db/music.db"

STREAM_THRESHOLDS = [3, 5]

COMPLETION_THRESHOLDS = [0.6, 0.8]

LIKE_PROBABILITIES = {
    2: 0.4,
    3: 0.75,
    4: 0.95
}


# Returns a list of dictionaries of the form
# {"user_id": ...,
#  "song_id": ...,
#  "total_streams": ...,
#  "total_ms_played": ...,
#  "completion_rate": ...,
#  "latest_stream": ...}
# from the "candidate_metrics" view within music.db.
def get_candidate_metrics(db_path = DB_PATH) -> list[dict]:

    with sqlite3.connect(db_path) as con:

        cur = con.cursor()
        cur.execute("""SELECT * FROM candidate_metrics
                       ORDER BY user_id ASC, song_id ASC
                    """)
        results = cur.fetchall()

        candidate_metrics = []

        for row in results:

            candidate = {
                "user_id": row[0],
                "song_id": row[1],
                "total_streams": row[2],
                "total_ms_played": row[3],
                "completion_rate": row[4],
                "latest_stream": row[5]
            }
            candidate_metrics.append(candidate)

        return candidate_metrics


# Expects the list of dictionaries returned by get_candidate_metrics().
# Appends each dictionary (candidate) with a score based on its
# total_streams and completion_rate.
# Also appends each dictionary with a like_probability based on the
# assigned score.
def score_candidates(candidate_metrics: list[dict]) -> list[dict]:

    for candidate in candidate_metrics:

        score = 0

        if candidate["total_streams"] >= STREAM_THRESHOLDS[0]:
            score += 1
        if candidate["total_streams"] >= STREAM_THRESHOLDS[1]:
            score += 1
        if candidate["completion_rate"] >= COMPLETION_THRESHOLDS[0]:
            score += 1
        if candidate["completion_rate"] >= COMPLETION_THRESHOLDS[1]:
            score += 1

        if score == 2:
            probability = LIKE_PROBABILITIES[2]
        elif score == 3:
            probability = LIKE_PROBABILITIES[3]
        elif score >= 4:
            probability = LIKE_PROBABILITIES[4]
        else:
            probability = 0

        candidate["score"] = score
        candidate["like_probability"] = probability

    return candidate_metrics


# Expects the scored list of dictionaries returned by score_candidates().
# Evaluates probabilities of candidates and decides inclusion in liked_songs.
# Returns liked_songs as a list of tuples (user_id, song_id).
def generate_liked_songs(scored_candidates: list[dict]) -> list[tuple[int, int]]:

    liked_songs = []

    for candidate in scored_candidates:

        if random.random() < candidate["like_probability"]:
            liked_songs.append((candidate["user_id"], candidate["song_id"], candidate["latest_stream"]))

    return liked_songs


# Inserts (user_id, song_id, latest_stream) triplets from the liked_songs list of tuples
# returned by generate_liked_songs into the "liked_songs" table using
# the specified database path.
def seed_liked_songs(db_path = DB_PATH):

    liked_songs = generate_liked_songs(score_candidates(get_candidate_metrics()))

    with sqlite3.connect(db_path) as con:

        cur = con.cursor()

        cur.executemany("""
            INSERT OR IGNORE INTO liked_songs (user_id, song_id, liked_datetime)
            VALUES (?, ?, ?)
        """, liked_songs)

        con.commit()

    print(f"{len(liked_songs)} liked songs seeded.")


if __name__ == "__main__":
    seed_liked_songs()





