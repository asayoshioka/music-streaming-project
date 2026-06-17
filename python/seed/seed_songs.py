import csv
import sqlite3
from get_ids import get_id_map, get_album_ids

# Iterate through tracks.csv
# Store (track_id, track_name, album, duration_ms) tuples in a list
# Get album IDs from existing SQLite "albums" table
# Insert (track_id, track name, album_id, duration_ms) into the "songs" table within "music.db"

DB_PATH = "/workspaces/music-streaming-project/db/music.db"
CSV_PATH = "/workspaces/273640407/music_db_project/python/data_pipeline/tracks.csv"


def seed_songs():

    # Build python lookup dictionary for albums
    album_map = get_album_ids()

    # Build python lookup dictionary for artists
    artist_map = get_id_map(table="artists")

    # List of songs (tuples) for insertion
    songs = []

    with open(CSV_PATH, "r", newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            track_id = row["track_id"]
            track_name = row["track_name"]
            album = row["album"]
            artist = row["artist"]
            duration_ms = row["duration_ms"]
            artist_id = artist_map[artist]
            album_id = album_map[(album, artist_id)]

            songs.append((track_id, track_name, album_id, duration_ms))

    with sqlite3.connect(DB_PATH) as con:

        cur = con.cursor()

        cur.executemany("""
            INSERT OR IGNORE INTO "songs" ("spotify_id", "name", "album_id", "duration_ms")
            VALUES
            (?, ?, ?, ?)
            """,
            songs
        )
        con.commit()

    print(f"{len(songs)} songs seeded.")


if __name__ == "__main__":
    seed_songs()
