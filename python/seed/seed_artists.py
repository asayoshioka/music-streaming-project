import csv
import sqlite3

# Iterate through tracks.csv
# Store unique artists as tuples in a list
# Insert artists from the list into the "artists" table within music.db

# Note: some artists may have the same name, so this process may collapse
# artists into one entity in the "artists" table.

DB_PATH = "/workspaces/music-streaming-project/db/music.db"
CSV_PATH = "/workspaces/273640407/music_db_project/python/data_pipeline/tracks.csv"

def seed_artists():

    seen = set()
    artists = []

    with open(CSV_PATH, "r", newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            artist = row["artist"].strip()

            if artist not in seen:
                seen.add(artist)
                artists.append((artist,))

    with sqlite3.connect(DB_PATH) as con:

        cur = con.cursor()

        cur.executemany("""
            INSERT OR IGNORE INTO "artists" ("name")
            VALUES (?)
        """, artists)

        con.commit()

    print(f"{len(artists)} artists seeded.")

if __name__ == "__main__":
    seed_artists()
