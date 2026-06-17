import csv
import sqlite3
from get_ids import get_id_map

# Iterate through tracks.csv
# Store unique (album, artist) pairs as tuples in a list
# Insert album names and their corresponding artist from the list into the "albums" table within music.db

DB_PATH = "/workspaces/music-streaming-project/db/music.db"
CSV_PATH = "/workspaces/273640407/music_db_project/python/data_pipeline/tracks.csv"

def seed_albums():

    # Get python dictionary for artist IDs
    artist_map = get_id_map(table="artists")
    seen = set()
    albums = []

    with open(CSV_PATH, "r", newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:
            artist = row["artist"]
            artist_id = artist_map[artist]
            album = row["album"]
            if (album, artist_id) not in seen:
                seen.add((album, artist_id))
                albums.append((album, artist_id))

    with sqlite3.connect(DB_PATH) as con:

        cur = con.cursor()

        cur.executemany("""
            INSERT OR IGNORE INTO "albums" ("name", "artist_id")
            VALUES (?, ?)
            """, albums)

        con.commit()

    print(f"{len(albums)} albums seeded.")


if __name__ == "__main__":
    seed_albums()
