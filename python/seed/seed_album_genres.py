import sqlite3
import csv
from get_ids import get_id_map, get_album_ids

DB_PATH = "/workspaces/music-streaming-project/db/music.db"
CSV_PATH = "/workspaces/273640407/music_db_project/python/data_pipeline/tracks.csv"

# Iterate through tracks.csv
# Extract unique (album, artist, genre) tuples
# Map (album, artist) -> album_id
# Insert (album_id, genre_id) into "album_genres" within music.db


def seed_album_genres():

    # Build python dict for albums:
    # album_map[(album, artist_id)] = album_id
    album_map = get_album_ids()

    # Build python dict for genre ids
    genre_map = get_id_map(table="genres")

    # Build python dict for artist ids
    artist_map = get_id_map(table="artists")

    # List of tuples (album_id, genre_id) for insertion
    album_genres = []

    seen = set()

    with open(CSV_PATH, "r", newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            album = row["album"].strip()
            artist = row["artist"].strip()
            genre = row["track_genre"].strip()

            artist_id = artist_map[artist]
            album_id = album_map[(album, artist_id)]
            genre_id = genre_map[genre]

            key = (album_id, genre_id)

            if key not in seen:
                seen.add(key)
                album_genres.append(key)

    with sqlite3.connect(DB_PATH) as con:

        cur = con.cursor()

        cur.executemany("""
            INSERT OR IGNORE INTO "album_genres" ("album_id","genre_id")
            VALUES (?, ?)
        """, album_genres)

        con.commit()

    print(f"{len(album_genres)} album-genre pairs seeded.")


if __name__ == "__main__":
    seed_album_genres()
