# Database Design — Music Streaming Platform

This document covers the schema design, table relationships, and key design decisions for the SQLite database underlying the music streaming analytics platform.

---

## Entity-Relationship Overview

The schema models the core entities of a music streaming platform and the relationships between them.

**Core entities:** `users`, `artists`, `albums`, `songs`, `genres`

**Activity tables:** `streams`, `liked_songs`, `liked_albums`

**Junction tables (many-to-many):** `song_credits`, `album_credits`, `song_genres`, `album_genres`

---

## Schema

### `users`

Represents registered users on the platform.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `username` | TEXT | NOT NULL, UNIQUE |
| `country` | TEXT | NOT NULL |
| `subscription_type` | TEXT | NOT NULL, CHECK IN ('free', 'premium') |
| `signup_date` | TEXT | NOT NULL |

---

### `artists`

Represents musical artists.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `name` | TEXT | NOT NULL |

---

### `albums`

Represents albums. Albums are linked to a primary artist via `artist_id` to ensure uniqueness — see [Design Decisions](#design-decisions).

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `name` | TEXT | NOT NULL |
| `artist_id` | INTEGER | NOT NULL |
| `release_date` | TEXT | — |

---

### `songs`

Represents individual tracks. Songs may belong to an album or exist independently.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `spotify_id` | TEXT | NOT NULL, UNIQUE |
| `name` | TEXT | NOT NULL |
| `album_id` | INTEGER | FK → albums(id), ON DELETE SET NULL |
| `track_number` | INTEGER | CHECK > 0 |
| `duration_ms` | INTEGER | NOT NULL, CHECK > 0 |
| `release_date` | TEXT | — |
| `lyrics` | TEXT | — |

---

### `genres`

Represents genre categories.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `name` | TEXT | NOT NULL, UNIQUE |

---

### `streams`

Records individual song plays. The `skipped` column is a generated column derived from `ms_played`.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `user_id` | INTEGER | NOT NULL, FK → users(id), ON DELETE SET NULL |
| `song_id` | INTEGER | NOT NULL, FK → songs(id), ON DELETE CASCADE |
| `start_datetime` | TEXT | NOT NULL |
| `ms_played` | INTEGER | NOT NULL, CHECK > 0 |
| `skipped` | INTEGER | GENERATED: `ms_played < 30000` (VIRTUAL) |

---

### `liked_songs`

Junction table representing a user's liked songs. Each user-song pair is unique.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `user_id` | INTEGER | NOT NULL, FK → users(id) |
| `song_id` | INTEGER | NOT NULL, FK → songs(id) |
| `liked_datetime` | TEXT | NOT NULL |
| — | — | UNIQUE(user_id, song_id) |

---

### `liked_albums`

Junction table representing a user's liked albums. Each user-album pair is unique.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `user_id` | INTEGER | NOT NULL, FK → users(id) |
| `album_id` | INTEGER | NOT NULL, FK → albums(id) |
| `liked_datetime` | TEXT | NOT NULL |
| — | — | UNIQUE(user_id, album_id) |

---

### `song_credits`

Junction table for artist credits on songs. Supports multiple artists per song with a role field.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `song_id` | INTEGER | NOT NULL, FK → songs(id), ON DELETE CASCADE |
| `artist_id` | INTEGER | NOT NULL, FK → artists(id), ON DELETE CASCADE |
| `role` | TEXT | NOT NULL (e.g. 'Main Artist') |

---

### `album_credits`

Junction table for artist credits on albums.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `album_id` | INTEGER | NOT NULL, FK → albums(id), ON DELETE CASCADE |
| `artist_id` | INTEGER | NOT NULL, FK → artists(id), ON DELETE CASCADE |
| `role` | TEXT | NOT NULL |

---

### `song_genres`

Junction table linking songs to genres. Each song-genre pair is unique.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `song_id` | INTEGER | NOT NULL, FK → songs(id), ON DELETE CASCADE |
| `genre_id` | INTEGER | NOT NULL, FK → genres(id), ON DELETE CASCADE |
| — | — | UNIQUE(song_id, genre_id) |

---

### `album_genres`

Junction table linking albums to genres. Each album-genre pair is unique.

| Column | Type | Constraints |
|---|---|---|
| `id` | INTEGER | PRIMARY KEY |
| `album_id` | INTEGER | NOT NULL, FK → albums(id), ON DELETE CASCADE |
| `genre_id` | INTEGER | NOT NULL, FK → genres(id), ON DELETE CASCADE |
| — | — | UNIQUE(album_id, genre_id) |

---

## Relationships

```
users ──< streams >── songs
users ──< liked_songs >── songs
users ──< liked_albums >── albums

songs >── albums
albums >── artists (via artist_id)

songs ──< song_credits >── artists
songs ──< song_genres >── genres

albums ──< album_credits >── artists
albums ──< album_genres >── genres
```

---

## Design Decisions

### Multi-artist support via junction tables

Songs and albums support multiple contributing artists through `song_credits` and `album_credits`. Each credit includes a `role` field (e.g. `'Main Artist'`, `'Featured'`) rather than flattening collaborators into a single text field. This preserves the ability to query by artist across both solo and collaborative works.

### Album deduplication using `artist_id`

Album titles are not unique — the same title (e.g. *Greatest Hits*) can belong to multiple unrelated artists. The source Kaggle dataset did not include album identifiers, so there was no reliable key to distinguish them during loading.

To prevent unrelated albums from being merged into a single record, an `artist_id` column was added directly to the `albums` table. Albums are deduplicated on `(name, artist_id)` during the ETL process. This was an adaptation made during pipeline development to accommodate a real-world data quality limitation.

### Generated column for skip detection

Rather than computing skip status at query time or storing a redundant boolean, `streams.skipped` is a `VIRTUAL GENERATED ALWAYS` column derived from `ms_played < 30000` (i.e. less than 30 seconds played). This keeps skip logic consistent across all queries without requiring application-layer logic.

### Deletion behavior

- `streams.user_id` uses `ON DELETE SET NULL` — streams are retained for analytics even if a user is deleted
- `streams.song_id` uses `ON DELETE CASCADE` — streams are removed if their song is removed
- All junction table foreign keys use `ON DELETE CASCADE` to maintain referential integrity automatically

### Normalization

The schema is normalized to third normal form (3NF). Genre, artist, and album information is stored once and referenced by ID, avoiding duplication across song records. The junction table pattern handles all many-to-many relationships cleanly.

---

## Indexes

Indexes were added on columns involved in the most frequent joins and filters across the Streamlit application.

| Index | Table | Column(s) | Rationale |
|---|---|---|---|
| `index_streams_user_id` | `streams` | `user_id` | Filters streams by user across nearly every user-facing query |
| `index_streams_song_id` | `streams` | `song_id` | Joins streams to songs for top content and recommendation queries |
| `index_streams_user_song` | `streams` | `(user_id, song_id)` | Composite index for co-streaming lookups in collaborative filtering |
| `index_streams_start_datetime` | `streams` | `start_datetime` | Speeds time-based filtering (listening hour analysis, validation queries) |
| `index_song_genres_song_id` | `song_genres` | `song_id` | Joins songs to genres for affinity scoring |
| `index_song_genres_genre_id` | `song_genres` | `genre_id` | Looks up all songs in a genre for genre-based recommendations |
| `index_song_credits_song_id` | `song_credits` | `song_id` | Joins songs to artists for artist affinity and profile queries |
| `index_song_credits_artist_id` | `song_credits` | `artist_id` | Looks up all songs by an artist |

The `streams` table receives the most indexes because it is the largest table and is queried in almost every analytical view — for user behavior metrics, listening patterns, recommendation scoring, and similarity calculations.

---

## Planned / Future Work

- `liked_albums` is defined in the schema but not yet populated by the ETL or surfaced in the application
- Multi-artist tracks were excluded from the initial ETL pass (the schema supports them via `song_credits`)
