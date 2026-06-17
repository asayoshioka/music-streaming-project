------------------------------------------------------------------------------------
-- INDEXES
------------------------------------------------------------------------------------

CREATE INDEX index_streams_user_id ON streams(user_id);
CREATE INDEX index_streams_song_id ON streams(song_id);
CREATE INDEX index_streams_user_song ON streams(user_id, song_id);

CREATE INDEX index_song_genres_song_id ON song_genres(song_id);
CREATE INDEX index_song_genres_genre_id ON song_genres(genre_id);
CREATE INDEX index_song_credits_song_id ON song_credits(song_id);
CREATE INDEX index_song_credits_artist_id ON song_credits(artist_id);

CREATE INDEX index_streams_start_datetime ON streams(start_datetime);
