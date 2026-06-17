# 🎧 Music Streaming Analytics & Recommendation Platform

A Spotify-inspired music analytics and recommendation platform built from scratch using Python, SQLite, and Streamlit. The project simulates the data infrastructure and analytical systems that power modern music streaming services — combining real music metadata with a synthetically generated user base and listening behavior.

Built after completing HarvardX's CS50 courses in Python and SQL as a hands-on end-to-end data engineering project.

---

## Features

- **Collaborative filtering** — personalized song recommendations based on user similarity
- **Explainable recommendations** — scoring breakdowns that surface the reasoning behind each suggestion
- **Listener archetype classification** — behavioral segments like Explorer, Genre Loyalist, Night Listener, and more
- **Genre & artist affinity scoring** — quantified preference profiles per user
- **User similarity explorer** — compare users by listening overlap, replay behavior, and completion rates
- **Platform-wide analytics** — top content, listening trends, engagement metrics, and behavior distributions
- **SQL view-based analytics architecture** — reusable views power all profiling and recommendation logic

---

## Demo

<p align="center">
  <img src="https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExd2JtczFndm5teXV3azc1MjF1azAwc3FmMHplMWo2czN3bzBoNms0bSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/YoCswMGJTeCuPk5xp6/giphy.gif" width="800" />
</p>

---

## Tech Stack

| Layer | Technologies |
|---|---|
| Database | SQLite, schema normalization, SQL views, junction tables |
| Data engineering | Python, Pandas, ETL pipeline, synthetic data generation (Faker) |
| Analytics | SQL aggregation, collaborative filtering, behavioral modeling |
| Application | Streamlit, Altair |

---

## Project Structure

```
├── db/
│   ├── music.db                        # Primary SQLite database
│   ├── music_v1.db                     # Version 1 database
│   └── reset.sql                       # Schema reset script
├── raw_dataset.csv                     # Source Spotify tracks data
├── queries_and_views/
│   ├── v1/
│   │   ├── analytics_queries.sql
│   │   ├── recommendation_queries.sql
│   │   ├── user_profile_views.sql
│   │   ├── indexes.sql
│   │   └── validation_queries.sql
│   └── v2/
│       └── validation_queries_v2.sql
├── python/
│   ├── data_pipeline/
│   │   ├── build_dataset.py            # ETL pipeline
│   │   ├── tracks.csv                  # Cleaned intermediate dataset
│   │   └── tracks_v1.csv
│   ├── seed/                           # Database seeding scripts
│   │   ├── seed.py                     # Main seed entrypoint
│   │   ├── seed_genres.py
│   │   ├── seed_artists.py
│   │   ├── seed_albums.py
│   │   ├── seed_songs.py
│   │   ├── seed_song_genres.py
│   │   ├── seed_song_credits.py
│   │   ├── seed_album_genres.py
│   │   ├── seed_users.py
│   │   ├── seed_streams.py
│   │   ├── seed_liked_songs.py
│   │   ├── db_mappings.py
│   │   └── get_ids.py
│   ├── app/
│   │   ├── 0_Home.py                   # Streamlit entry point
│   │   ├── pages/
│   │   │   ├── 1_User_Taste_Profiles.py
│   │   │   ├── 2_Recommendation_Explorer.py
│   │   │   ├── 3_User_Similarity_Explorer.py
│   │   │   ├── 4_Music_Analytics.py
│   │   │   ├── 5_Listener_Archetypes.py
│   │   │   ├── 6_Database_&_ETL.py
│   │   │   └── 7_SQL_&_Analytics_Engineering.py
│   │   ├── utils/
│   │   │   ├── queries.py
│   │   │   ├── user_taste_profiles.py
│   │   │   ├── user_similarity.py
│   │   │   ├── recommendations.py
│   │   │   ├── get_ids_and_maps.py
│   │   │   ├── styles.py
│   │   │   └── __init__.py
│   │   └── assets/
│   │       ├── music_db_erd.html
│   │       ├── data_pipeline_flowchart.svg
│   │       ├── data_pipeline_flowchart_horizontal_wrap.svg
│   │       └── seeding_order_flow.svg
│   └── reset_db.py
├── requirements.txt
├── DESIGN.md
└── README.md
```

---

## Getting Started

### Live app

The app is publicly deployed and requires no setup to use:

**[🎧 Open the app →](https://asa-music-analytics.streamlit.app/)** 

### Run locally

If you'd like to run the project locally:

```bash
git clone https://github.com/asayoshioka/music-streaming-project.git
cd music-streaming-project
pip install -r python/requirements.txt
cd python/app
streamlit run python/app/0_Home.py
```

---

## How It Was Built

The project was developed across nine phases:

**Phase 1 — Database design.** Designed a normalized relational schema representing users, artists, albums, songs, genres, streams, and liked content. Many-to-many relationships (song credits, album credits, song genres) were modeled through junction tables. See [DESIGN.md](DESIGN.md) for the full schema and design decisions.

**Phase 2 — ETL pipeline.** Built a custom Python ETL pipeline to load ~90,000 Spotify tracks from a [Kaggle dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) into the database. Tables were seeded in dependency order to maintain foreign key integrity. One notable challenge: album titles are not unique in the source data and no album IDs were provided, so an `artist_id` field was incorporated into the albums table to prevent unrelated albums from being merged.

**Phase 3 — Synthetic user generation.** Generated 500 synthetic users with probabilistic attributes (country, subscription type, signup date) designed to mimic realistic platform distributions.

**Phase 4 — Listening behavior simulation.** Each user was assigned behavioral preferences (favorite genres, preferred listening hours, skip and replay tendencies) before streams were generated probabilistically using those preferences. This produced a realistic behavioral dataset rather than random noise.

**Phase 5 — Data validation & analytics.** Wrote SQL validation queries to check for logical errors (streams before signup dates, invalid completion rates, future timestamps) and developed platform-wide analytical queries covering top content, engagement patterns, and listening behavior.

**Phase 6 — Recommendation systems.** Implemented three approaches: song-to-song recommendations (co-streaming patterns), personalized user recommendations (collaborative filtering), and user similarity scoring. All use weighted scoring systems and are designed to be explainable rather than black-box.

**Phase 7 — User profiling.** Built a behavioral analytics layer using reusable SQLite views (genre affinity, artist affinity, diversity metrics, listening hours, behavior metrics). Python combines these views into structured taste profiles per user.

**Phase 8 — Listener archetypes.** Classified users into interpretable behavioral segments using their behavioral metrics. Users can belong to multiple archetypes simultaneously.

**Phase 9 — Streamlit dashboard.** Built a multipage interactive application exposing all of the above through visualizations and user-facing interfaces.

---

## Data Sources

- **Music metadata** — [Spotify Tracks Dataset](https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset) via Kaggle (~90,000 tracks)
- **Users, streams, and archetypes** — synthetically generated

---

## Skills Demonstrated

Relational database design · Schema normalization · ETL pipeline development · SQL query design · Data validation · Behavioral analytics · Synthetic data generation · Collaborative filtering · Recommendation systems · User profiling · Dashboard development · Data visualization · Python application development
