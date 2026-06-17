import sqlite3

DB_PATH = "/workspaces/273640407/music_db_project/db/music.db"

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


# Returns dict with key-value pairs of the form
# genre_id: [song1, song2, ...]
def get_songs_by_genre(db_path=DB_PATH):

    # Build a dict with key-value pairs of the form
    # song_id: genre_id
    song_genres_map = get_id_value_map(table="song_genres",
                                       id_column="song_id",
                                       value_column="genre_id"
                                        )

    # Build a songs_by_genre dict with key-value pairs of the form
    # genre_id: [song1, song2, song3]
    songs_by_genre = {}

    for song_id, genre_id in song_genres_map.items():

        if genre_id not in songs_by_genre:
            songs_by_genre[genre_id] = []

        songs_by_genre[genre_id].append(song_id)

    return(songs_by_genre)


# Returns dict with key-value pairs of the form
# artist_id: [song1, song2, ...]
def get_songs_by_artist(db_path=DB_PATH):

    # Build a dict with key-value pairs of the form
    # song_id: artist_id
    song_artists_map = get_id_value_map(table="song_credits",
                                        id_column="song_id",
                                        value_column="artist_id"
                                        )

    # Build a songs_by_artist dict with key-value pairs of the form
    # artist_id: [song1, song2, song3]
    songs_by_artist = {}

    for song_id, artist_id in song_artists_map.items():

        if artist_id not in songs_by_artist:
            songs_by_artist[artist_id] = []

        songs_by_artist[artist_id].append(song_id)

    return(songs_by_artist)


# Returns dict with key-value pairs of the form
# genre_id: [artist1, artist2, ...]
def get_artists_by_genre(db_path=DB_PATH):

    # Get table with "genre_id", "artist_id" columns

    with sqlite3.connect(db_path) as con:
        cur = con.cursor()
        query = """
                SELECT sg.genre_id, sc.artist_id
                FROM song_genres sg
                JOIN song_credits sc ON sg.song_id = sc.song_id
                GROUP BY sg.genre_id, sc.artist_id
                """
        cur.execute(query)
        rows = cur.fetchall()

    # Build dict with key-value pairs of the form
    # genre_id: [artist1, artist2, ...]
    artists_by_genre = {}

    for genre_id, artist_id in rows:

        if genre_id not in artists_by_genre:
            artists_by_genre[genre_id] = []

        artists_by_genre[genre_id].append(artist_id)

    return artists_by_genre


if __name__ == "__main__":
    map = get_artists_by_genre()
    for _ in map:
        print(f"genre: {_}\n artist_ids: {map[_]}\n")



