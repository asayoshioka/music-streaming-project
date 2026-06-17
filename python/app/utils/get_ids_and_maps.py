import sqlite3
from utils import DB_PATH


# DB_PATH = "/workspaces/music-streaming-project/db/music.db"

# Returns dict with key-value pairs of the form
# id_column: value_column
def get_id_value_map(table: str, value_column: str,
                     id_column: str = "id", db_path: str = DB_PATH) -> dict:

    with sqlite3.connect(db_path) as con:

        cur = con.cursor()
        query = f"""
                 SELECT {id_column}, {value_column} FROM {table}
                 ORDER BY {id_column}
                 """
        cur.execute(query)
        return dict(cur.fetchall())


# Returns tuple of user ids in ascending order
def get_user_ids(db_path: str = DB_PATH):

    with sqlite3.connect(db_path) as con:

        cur = con.cursor()
        cur.execute("SELECT id FROM users ORDER BY id ASC")
        user_ids = tuple(row[0] for row in cur.fetchall())

    return user_ids


# Returns a song id, given a song's title and artist
def get_song_id(song_title: str, artist: str, db_path: str = DB_PATH):

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = f"""SELECT songs.id
                   FROM songs
                   JOIN song_credits sc ON songs.id = sc.song_id
                   JOIN artists on sc.artist_id = artists.id
                   WHERE songs.name = ? AND
                         artists.name = ?
                """
        cur.execute(query, (song_title, artist))
        return cur.fetchone()[0]



if __name__ == "__main__":
    # map = get_id_value_map(table="users", value_column="username")
    # for user in map:
    #     print(f"id: {user}, username: {map[user]}")
    print(get_song_id(song_title="thank u, next", artist="Ariana Grande"))
