import csv
import sqlite3

# Iterate through tracks.csv
# Store unique genres as tuples in a list
# Insert genres from the list into the "genres" table within music.db

DB_PATH = "/workspaces/273640407/music_db_project/db/music.db"
CSV_PATH = "/workspaces/273640407/music_db_project/python/data_pipeline/tracks.csv"

def seed_genres():

    seen = set()
    genres = []

    with open(CSV_PATH, "r", newline="", encoding="utf-8") as file:

        reader = csv.DictReader(file)

        for row in reader:

            genre = row["track_genre"]

            if genre not in seen:
                seen.add(genre)
                genres.append((genre,))

    with sqlite3.connect(DB_PATH) as con:

        cur = con.cursor()

        cur.executemany("""
            INSERT OR IGNORE INTO "genres" ("name")
            VALUES (?)
        """, genres)

        con.commit()

    print(f"{len(genres)} genres seeded.")


if __name__ == "__main__":
    seed_genres()
