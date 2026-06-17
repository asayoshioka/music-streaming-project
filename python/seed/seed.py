from seed_users import seed_users
from seed_albums import seed_albums
from seed_artists import seed_artists
from seed_genres import seed_genres
from seed_songs import seed_songs
from seed_song_genres import seed_song_genres
from seed_album_genres import seed_album_genres
from seed_song_credits import seed_song_credits
from seed_streams import seed_streams

def main():
    seed_genres()
    seed_artists()
    seed_albums()
    seed_songs()
    seed_song_genres()
    seed_album_genres()
    seed_song_credits()
    seed_streams()


if __name__ == "__main__":
    main()
