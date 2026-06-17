import sqlite3

DB_PATH = "/workspaces/music-streaming-project/db/music.db"

# Returns a dict with key-value pairs of the form
# key_column: id
def get_id_map(table: str, key_column: str = "name", db_path: str = DB_PATH) -> dict:

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute(f"SELECT {key_column}, id FROM {table} ORDER BY id")
        results = cur.fetchall()
        return dict(results)


# Returns a dict with key-value pairs of the form
# (album, artist_id): album_id
def get_album_ids(db_path=DB_PATH) -> dict:

    album_map = {}
    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        cur.execute("""
            SELECT id, name, artist_id
            FROM albums
            ORDER BY id
        """)
        albums = cur.fetchall()

        for album in albums:
            album_map[(album[1], album[2])] = album[0]

    return album_map


if __name__ == "__main__":
    ...
