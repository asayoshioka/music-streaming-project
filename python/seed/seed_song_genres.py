import sqlite3
import csv
from get_ids import get_id_map

DB_PATH = "/workspaces/273640407/music_db_project/db/music.db"
CSV_PATH = "/workspaces/273640407/music_db_project/python/data_pipeline/tracks.csv"

# Iterate through tracks.csv
# For each track, insert the corresponding song_id and genre_id
# into the song_genres table within music.db

def seed_song_genres():

    # Build python dict for a song's spotify id and its corresponding songs.id:
    # song_map[spotify_id] = song_id
    song_map = get_id_map(table="songs", key_column="spotify_id")

    # Build python dict for genre ids
    genre_map = get_id_map(table="genres")

    # List of tuples (song_id, genre_id) for insertion
    song_genres = []

    with open(CSV_PATH, "r", newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:
            spotify_id = row["track_id"]
            song_id = song_map[spotify_id]
            genre = row["track_genre"]
            genre_id = genre_map[genre]
            song_genres.append((song_id, genre_id))

    with sqlite3.connect(DB_PATH) as con:
        cur = con.cursor()
        cur.executemany("""
            INSERT OR IGNORE INTO "song_genres" ("song_id","genre_id")
            VALUES (?, ?)
        """, song_genres)
        con.commit()

    print(f"{len(song_genres)} song-genre pairs seeded.")


if __name__ == "__main__":
    seed_song_genres()
