import csv
import sqlite3
from get_ids import get_id_map

# Iterate through tracks.csv
# Store (track_name, artist) tuples in a list
# Get song and artist IDs from existing SQLite "songs" and "artists" tables
# Insert (song ID, artist ID, role) into the "song_credits" table within "music.db"

DB_PATH = "/workspaces/273640407/music_db_project/db/music.db"
CSV_PATH = "/workspaces/273640407/music_db_project/python/data_pipeline/tracks.csv"


def seed_song_credits():

    # Build python dict for a song's spotify id and its corresponding songs.id:
    # song_map[spotify_id] = song_id
    song_map = get_id_map(table="songs", key_column="spotify_id")

    # Build python lookup dictionary for artists
    artist_map = get_id_map(table="artists")

    # List of song-credit pairs (tuples) for insertion
    song_credits = []

    with open(CSV_PATH, "r", newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            spotify_id = row["track_id"]
            artist = row["artist"]

            song_id = song_map[spotify_id]
            artist_id = artist_map[artist]

            # Each song in tracks.csv has one main artist
            song_credits.append((song_id, artist_id, "Main Artist"))

    with sqlite3.connect(DB_PATH) as con:

        cur = con.cursor()

        cur.executemany("""
            INSERT OR IGNORE INTO "song_credits" ("song_id", "artist_id", "role")
            VALUES (?, ?, ?)
        """, song_credits)

        con.commit()

    print(f"{len(song_credits)} song-credit pairs seeded.")


if __name__ == "__main__":
    seed_song_credits()
