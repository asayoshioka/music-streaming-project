import sqlite3
import random
from datetime import date, time, datetime, timedelta
from get_ids import get_id_map
from db_mappings import (get_id_value_map,
                         get_songs_by_genre,
                         get_songs_by_artist,
                         get_artists_by_genre)

DB_PATH = "/workspaces/273640407/music_db_project/db/music.db"

PLATFORM_LAUNCH = datetime(2020, 1, 1)

random.seed(42)

# Dict with (user_id: signup_date) key-value pairs
USER_SIGNUP_MAP = get_id_value_map(table="users", value_column="signup_date")
# Dict with (song_id: duration_ms) key-value pairs
SONG_DURATION_MAP = get_id_value_map(table="songs", value_column="duration_ms")
# Dict with (genre_id: [song1, song2, ...]) key-value pairs
SONGS_BY_GENRE = get_songs_by_genre()
# Dict with(artist_id: [song1, song2, ...]) key-value pairs
SONGS_BY_ARTIST = get_songs_by_artist()
# Dict with(genre_id: [artist1, artist2, ...]) key-value pairs
ARTISTS_BY_GENRE = get_artists_by_genre()
# Dict with (spotify_id: song_id) key-value pairs
SONG_MAP = get_id_map(table="songs", key_column="spotify_id")
# Dict with (genre: id) key-value pairs
GENRE_MAP = get_id_map(table="genres", key_column="name")
# Dict with (username: id) key-value pairs
USER_MAP = get_id_map(table="users", key_column="username")

# List of all necessary ids
SONG_IDS = list(SONG_MAP.values())
GENRE_IDS = list(GENRE_MAP.values())
USER_IDS = list(USER_MAP.values())


ACTIVE_HOURS = {
    "day" : [9,10,11,12,13,14],
    "night": [20,21,22,23,0,1]
}

ACTIVITY_LEVELS = ["light", "medium", "heavy"]

# Returns dictionary with key-value pairs of the form
# {user_id: {"favorite_genres": [...],
#            "favorite_artists": [...],
#            "listener_type": [...],
#            "skip_rate": ...},
#            "replay_tendency": ...,
#            "exploration_rate": ...,
#            "activity_level": ...}
# "favorite_genres": includes 1 to 3 random genre ids
# "favorite_artists": includes at least 1 artist id based on favorite genre(s)
# "listener_type": "day" or "night"
# "skip_rate": between 0.05 and 0.4 -- e.g. 0.05 --> rarely skips
# "replay_tendency": between 0.05 and 0.35 -- e.g. 0.05 --> rarely replays
# "exploration_rate": between 0.2 and 0.7 -- e.g. 0.1 --> mostly favorites
# "activity_level": "light", "medium", or "heavy"
def build_user_profiles(user_ids: list = USER_IDS, genre_ids: list = GENRE_IDS) -> dict:

    user_profiles = {}

    for user_id in user_ids:

        favorite_genres = random.sample(genre_ids, random.randint(1,3))

        # Assign favorite artists based on favorite genres

        favorite_artists = []

        # For each favorite genre, try to add at least 2 favorite artists
        for genre in favorite_genres:

            artists = ARTISTS_BY_GENRE[genre]

            if artists:
                favorite_artists.extend(random.sample(artists, min(2, len(artists))))

        # Deduplicate favorite artists
        favorite_artists = list(set(favorite_artists))

        user_profile = {
            "favorite_genres": favorite_genres,
            "favorite_artists": favorite_artists,
            "listener_type": random.choice(["day", "night"]),
            "skip_rate": round(random.uniform(0.05, 0.4), 2),
            "replay_tendency": round(random.uniform(0.05, 0.35), 2),
            "exploration_rate": round(random.uniform(0.2, 0.7), 2),
            "activity_level": random.choices(ACTIVITY_LEVELS,
                                             weights=[0.4, 0.4, 0.2])[0]
        }

        user_profiles[user_id] = user_profile


    return user_profiles


# Generates one song id given a particular user's id, their profile, and a
# user_history dict with ("user_id": [song1, song2, ...]) key-value pairs
def generate_song_id(user_id: int, profile: dict, user_history: dict) -> int:

    # Get specific user's history -- if none yet, return an empty list.
    # history contains a list of streamed songs
    history = user_history.get(user_id, [])

    # Cap replay selection to recent history
    recent_history = history[-50:]

    # 1. Replay behavior
    if recent_history and random.random() < profile["replay_tendency"]:
            return random.choice(history)

    # 2. Exploration behavior
    if random.random() < profile["exploration_rate"]:
        return random.choice(SONG_IDS)

    # 3. Favorite artist behavior
    if profile["favorite_artists"] and random.random() < 0.6:

        artist_id = random.choice(profile["favorite_artists"])

        if SONGS_BY_ARTIST.get(artist_id):
            return random.choice(SONGS_BY_ARTIST[artist_id])

    # 4. Favorite genre behavior (default)
    genre_id = random.choice(profile["favorite_genres"])

    return random.choice(SONGS_BY_GENRE[genre_id])


# Returns a random startdatetime at which a stream begins,
# based on a user's listener_type ("night" or "day") and signup_date.
# TIME MODEL: bias toward recent dates
# NOTE: user signup_dates have been restricted from PLATFORM_LAUNCH to at latest TWO YEARS AGO
# from the current date to support this model, i.e., to ensure streams occur AFTER signup.
def generate_start_datetime(listener_type: str, signup_date: datetime = PLATFORM_LAUNCH) -> str:

    today = date.today()

    # 1. Choose a day -- 40% within last month, 40% within last year, 20% older

    val = random.random()

    if val < 0.4:
        random_days = random.randint(0,30)
        random_date = today - timedelta(days=random_days)
    elif val < 0.8:
        random_days = random.randint(0,365)
        random_date = today - timedelta(days=random_days)
    else:
        # Find days between signup_date and 1 year ago
        year_ago_date = today - timedelta(days=365)
        year_ago_datetime = datetime.combine(year_ago_date, datetime.min.time())
        days = (year_ago_datetime - signup_date).days

        random_days = random.randint(0,days)
        # Add one day to ensure streams always occur after signup
        random_date = signup_date + timedelta(days=random_days + 1)

    # 2. Choose an hour -- 70% preferred hours, 30% random hours
    if random.random() < 0.7:
        random_hour = random.choice(ACTIVE_HOURS[listener_type])
    else:
        random_hour = random.randint(0,23)

    random_time = time(random_hour, random.randint(0,59), random.randint(0,59))
    random_datetime = datetime.combine(random_date,random_time)

    return random_datetime.strftime("%Y-%m-%d %H:%M:%S")


# Generate random ms_played given a user's skip_rate and a song's duration_ms
def generate_ms_played(skip_rate: float, duration_ms: int) -> int:
    # The probability of a random float in [0,1) being less than skip_rate is skip_rate.
    # In this event, ms_played will be b/t 5 and 29 seconds (a skip)
    # Note: no songs in the dataset are shorter than 30 seconds
    if random.random() < skip_rate:
        ms_played = random.randint(5000, 29000)
    else:
        ms_played = random.randint(30000, duration_ms)

    return ms_played


# Generate ONE stream given a user's id, their profile, and a
# user_history dict with ("user_id": [song1, song2, ...]) key-value pairs
def generate_stream(user_id: int, profile: dict, user_history: dict):

    # Get user's signup date
    signup_date = USER_SIGNUP_MAP[user_id]

    # Convert signup_date to a datetime object.
    # (signup datetimes retrieved from database will be returned as strings)
    signup_date = datetime.strptime(signup_date, '%Y-%m-%d %H:%M:%S')

    song_id = generate_song_id(user_id=user_id,
                               profile=profile,
                               user_history=user_history)

    start_datetime = generate_start_datetime(listener_type=profile["listener_type"],
                                             signup_date=signup_date)

    duration_ms = SONG_DURATION_MAP[song_id]

    ms_played = generate_ms_played(profile["skip_rate"], duration_ms)

    return (user_id, song_id, start_datetime, ms_played)


# Generate a random amount of streams for ALL users
def generate_streams():

    user_profiles = build_user_profiles()

    user_history = {}

    streams = []

    for user_id, profile in user_profiles.items():

        user_history[user_id] = []

        # Generate streams based on user's activity level
        if profile["activity_level"] == "light":
            stream_count = random.randint(50,150)
        elif profile["activity_level"] == "medium":
            stream_count = random.randint(150,400)
        else:
            stream_count = random.randint(400,1000)

        for _ in range(stream_count):

            stream = generate_stream(
                        user_id=user_id,
                        profile=profile,
                        user_history=user_history
                        )

            streams.append(stream)

            user_history[user_id].append(stream[1])

    return streams


# Seeds list of streams in "streams" within music.db
def seed_streams():

    streams = generate_streams()

    with sqlite3.connect(DB_PATH) as con:

        cur = con.cursor()

        cur.executemany(
            """
            INSERT INTO streams (user_id, song_id, start_datetime, ms_played)
            VALUES (?, ?, ?, ?)
            """,
            streams
        )

        con.commit()
        # Return the number of streams seeded
        print(f"{len(streams)} streams seeded.")


if __name__ == "__main__":
    seed_streams()

