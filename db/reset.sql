DROP TABLE IF EXISTS "users";
DROP TABLE IF EXISTS "albums";
DROP TABLE IF EXISTS "songs";
DROP TABLE IF EXISTS "genres";
DROP TABLE IF EXISTS "album_genres";
DROP TABLE IF EXISTS "song_genres";
DROP TABLE IF EXISTS "artists";
DROP TABLE IF EXISTS "song_credits";
DROP TABLE IF EXISTS "album_credits";
DROP TABLE IF EXISTS "streams";
DROP TABLE IF EXISTS "liked_songs";
DROP TABLE IF EXISTS "liked_albums";


-- Represent users on the music streaming platform
CREATE TABLE "users" (
    "id" INTEGER,
    "username" TEXT NOT NULL UNIQUE,
    "country" TEXT NOT NULL,
    "subscription_type" TEXT NOT NULL CHECK ("subscription_type" IN ('free', 'premium')),
    "signup_date" TEXT NOT NULL,
    PRIMARY KEY("id")
);

-- Represent albums on the music streaming platform
CREATE TABLE "albums" (
    "id" INTEGER,
    "name" TEXT NOT NULL,
    "artist_id" INTEGER NOT NULL,
    "release_date" TEXT,
    PRIMARY KEY("id")
);

-- Represent songs on the music streaming platform
CREATE TABLE "songs" (
    "id" INTEGER,
    "spotify_id" TEXT NOT NULL UNIQUE,
    "name" TEXT NOT NULL,
    "album_id" INTEGER, -- (if applicable)
    "track_number" INTEGER CHECK ("track_number" > 0), -- (if applicable)
    "duration_ms" INTEGER NOT NULL CHECK ("duration_ms" > 0),
    "release_date" TEXT,
    "lyrics" TEXT,
    PRIMARY KEY("id"),
    FOREIGN KEY("album_id") REFERENCES "albums"("id") ON DELETE SET NULL
);

-- Represent genres on the music streaming platform
CREATE TABLE "genres" (
    "id" INTEGER,
    "name" TEXT NOT NULL UNIQUE,
    PRIMARY KEY("id")
);

-- Represent album genres on the music streaming platform
CREATE TABLE "album_genres" (
    "id" INTEGER,
    "album_id" INTEGER NOT NULL,
    "genre_id" INTEGER NOT NULL,
    PRIMARY KEY("id"),
    FOREIGN KEY("album_id") REFERENCES "albums"("id") ON DELETE CASCADE,
    FOREIGN KEY("genre_id") REFERENCES "genres"("id") ON DELETE CASCADE,
    UNIQUE("album_id", "genre_id")
);

-- Represent song genres on the music streaming platform
CREATE TABLE "song_genres" (
    "id" INTEGER,
    "song_id" INTEGER NOT NULL,
    "genre_id" INTEGER NOT NULL,
    PRIMARY KEY("id"),
    FOREIGN KEY("song_id") REFERENCES "songs"("id") ON DELETE CASCADE,
    FOREIGN KEY("genre_id") REFERENCES "genres"("id") ON DELETE CASCADE,
    UNIQUE("song_id", "genre_id")
);

-- Represent artists on the music streaming platform
CREATE TABLE "artists" (
    "id" INTEGER,
    "name" TEXT NOT NULL,
    PRIMARY KEY("id")
);

-- Represent artist credits on songs
CREATE TABLE "song_credits" (
    "id" INTEGER,
    "song_id" INTEGER NOT NULL,
    "artist_id" INTEGER NOT NULL,
    "role" TEXT NOT NULL, -- (e.g. 'Main Artist')
    PRIMARY KEY("id"),
    FOREIGN KEY("song_id") REFERENCES "songs"("id") ON DELETE CASCADE,
    FOREIGN KEY("artist_id") REFERENCES "artists"("id") ON DELETE CASCADE
);

-- Represent artist credits on albums
CREATE TABLE "album_credits" (
    "id" INTEGER,
    "album_id" INTEGER NOT NULL,
    "artist_id" INTEGER NOT NULL,
    "role" TEXT NOT NULL,
    PRIMARY KEY("id"),
    FOREIGN KEY("album_id") REFERENCES "albums"("id") ON DELETE CASCADE,
    FOREIGN KEY("artist_id") REFERENCES "artists"("id") ON DELETE CASCADE
);

-- Represent streams on the music streaming platform
CREATE TABLE "streams" (
    "id" INTEGER,
    "user_id" INTEGER NOT NULL,
    "song_id" INTEGER NOT NULL,
    "start_datetime" TEXT NOT NULL,
    "ms_played" INTEGER NOT NULL CHECK ("ms_played" > 0),
    -- Automatically determine skip status using a generated column
    "skipped" INTEGER GENERATED ALWAYS AS ("ms_played" < 30000) VIRTUAL,
    PRIMARY KEY("id"),
    FOREIGN KEY("user_id") REFERENCES "users"("id") ON DELETE SET NULL,
    FOREIGN KEY("song_id") REFERENCES "songs"("id") ON DELETE CASCADE
);

CREATE TABLE "liked_songs" (
    "id" INTEGER,
    "user_id" INTEGER NOT NULL,
    "song_id" INTEGER NOT NULL,
    "liked_datetime" TEXT NOT NULL,
    PRIMARY KEY("id"),
    FOREIGN KEY("user_id") REFERENCES "users"("id"),
    FOREIGN KEY("song_id") REFERENCES "songs"("id"),
    UNIQUE("user_id", "song_id")
);

CREATE TABLE "liked_albums" (
    "id" INTEGER,
    "user_id" INTEGER NOT NULL,
    "album_id" INTEGER NOT NULL,
    "liked_datetime" TEXT NOT NULL,
    PRIMARY KEY("id"),
    FOREIGN KEY("user_id") REFERENCES "users"("id"),
    FOREIGN KEY("album_id") REFERENCES "albums"("id"),
    UNIQUE("user_id", "album_id")
);

-- Indexes to speed common searches

