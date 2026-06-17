import streamlit as st
import pandas as pd
import numpy as np
import sqlite3
from utils import ERD

# CSS for grey container 1
css = """
    <style>
    .st-key-grey_container {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """
st.html(css)

# CSS for grey container 2
css = """
    <style>
    .st-key-grey_container_2 {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """
st.html(css)

# CSS for grey container 3
css = """
    <style>
    .st-key-grey_container_3 {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """
st.html(css)

# CSS for grey container 4
css = """
    <style>
    .st-key-grey_container_4 {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """
st.html(css)

# Custom CSS to limit space around the divider -- from Google AI
st.markdown(
    """
    <style>
    hr {
        margin-top: -0.7rem !important;
        margin-bottom: -2.0rem !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Set page title and layout
st.set_page_config(page_title="Music Analytics | Asa",
                   page_icon="🎧", layout="wide")

# Add a header
st.header(":green[:material/Database:] Database and ETL")
st.write("*:grey[How was the data created and structured?]*")

st.markdown("#### :green[:material/Schema:] Schema")
with st.container(border=True):
    st.markdown("###### :grey[ER Diagram]")
    st.iframe(f"{ERD}")

    st.markdown("###### Schema Overview")
    st.markdown("""
        :grey[The schema consists of 12 tables organized around five core entities — Users, Songs,
        Artists, Albums, and Genres — connected through junction tables that model many-to-many
        relationships. Junction tables include Song Credits, Album Credits, Song Genres, and Album
        Genres. The schema is designed to support multiple genres per song and album, and multiple
        artist contributors per song and album with explicit roles.]
                """)

with st.expander(":green[Key Design Decisions]"):
    col1, col2 = st.columns(2, border=True)
    with col1:
        st.markdown("""
        **:green-badge[:material/Album:] &nbsp; Multi-genre support**  <br> :grey[Songs and albums can belong to multiple genres via junction tables,
        reflecting the reality that genre boundaries are rarely clean. Currently each song maps to one
        genre due to dataset limitations, but the schema is designed to support more.]
                    """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        **:green-badge[:material/Group:] &nbsp; Multi-artist support w/ roles**  <br> :grey[Both songs and albums support multiple credited contributors
        with explicit roles. Album credits and song credits are separated because album-level roles (executive producer)
        are meaningfully different from song-level roles.]
                    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2, border=True)
    with col1:
        st.markdown("""
        **:green-badge[:material/Artist:] &nbsp; artist_id on albums**  <br> :grey[The Kaggle dataset provided no album identifiers, and album titles are not
        unique across artists. Adding `artist_id` to the albums table was necessary to distinguish albums with the
        same name by different artists.]
                    """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        **:green-badge[:material/Skip_Next:] &nbsp; Generated columns for skips**  <br> :grey[`skipped` is a virtual generated column computed automatically from
        `ms_played`, avoiding redundant data storage while making skip filtering convenient in queries.]
                    """, unsafe_allow_html=True)
    col1, col2 = st.columns(2, border=True)
    with col1:
        st.markdown("""
        **:green-badge[:material/No_Sim:] &nbsp; Nullable columns**  <br> :grey[`track_number`, `release_date`, and `lyrics` in the songs table are nullable to
        accommodate incomplete metadata. Release date and lyrics could enable richer recommendations in the
        future — by recency or lyrical themes — but were not available in the current dataset.]
                    """, unsafe_allow_html=True)
    with col2:
        st.markdown("""
        **:green-badge[:material/Music_Note_2:] &nbsp; album_genres redundancy** <br> :grey[Although album genres can be inferred from song genres, the album_genres
        table was included to support direct album-level genre queries without traversing songs.]
                    """, unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown("**:green-badge[:material/Forward:] &nbsp; Future Extensions**")
        st.markdown("""
            :grey[A playlists table would be a natural addition, allowing users to create and manage their own song collections.]
                    """)

st.space("small")

st.markdown("#### :green[:material/Conversion_Path:] ETL Pipeline")

kaggle_url = "https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset"

with st.container(border=True):
    col1, col2, col3 = st.columns([0.8,7,2])
    col1.markdown(":grey[**SOURCE**]")
    col2.markdown(f"[Spotify Tracks Dataset -- Kaggle]({kaggle_url})")
    col3.markdown(":grey[~90,000 tracks · CSV]")

col1, col2 = st.columns(2, border=True)

with col1:
    st.markdown("**:green[1 )] &nbsp; EXTRACTION**")
    st.divider()
    st.markdown(""":grey[Fields relevant to the project extracted.
                Three filters applied before writing to intermediate CSV:]""")
    st.markdown(":green-badge[drop nulls] :green-badge[popularity ≥ 70] :green-badge[single-artist only]")
    with st.container(key="grey_container_2"):

        col_a, col_b = st.columns([0.3,5])

        col_a.markdown(":grey[:material/Info:]")

        with col_b:
            st.markdown(""" **Design note** <br>
                :grey[Multi-artist tracks excluded to simplify normalization --
                supporting them would require
                resolving a many-to-many artist-track relationship at load time]
                        """, unsafe_allow_html=True)
with col2:
    st.markdown("**:green[2 )] &nbsp; TRANSFORMATION**")
    st.divider()
    st.markdown(""":grey[Flat CSV normalized into relational structure — artists, albums, songs, and
                genres separated into entities.]""")
    st.space("small")
    with st.container(key="grey_container_4"):

        col_a, col_b = st.columns([0.3,5])

        col_a.markdown(":grey[:material/Info:]")

        with col_b:
            st.markdown(""" **Design note** <br>
                :grey[Duplicates resolved at two levels to guard against constraint violations --
                first in memory with a `seen` set, then with `INSERT OR IGNORE` as a database-level safeguard.]
                        """, unsafe_allow_html=True)

with st.container(border=True):

    # st.markdown("##### :green[Data Source]")

    # st.markdown(f"""
    #     :grey[Music metadata was sourced from a [Spotify Tracks Dataset]({kaggle_url}) available on Kaggle,
    #     containing approximately 90,000 unique tracks with attributes including track name,
    #     artist, album, genre, popularity, and duration.]
    #             """)

    # st.markdown("##### :green[Extraction]")

    # st.markdown("""
    #     Only the fields relevant to the project were extracted from the raw CSV. To keep the dataset
    #     manageable and the data clean, two filters were applied during extraction: tracks with
    #     missing values were dropped, and only tracks with a popularity score of 70 or above were retained.
    #     Multi-artist tracks were excluded to simplify normalization, since supporting them would require
    #     resolving a many-to-many artist-track relationship at load time. After filtering, the dataset
    #     was deduplicated on (track name, artist) pairs to remove redundant entries before being written
    #     to an intermediate CSV file.
    #             """)

    # st.markdown("##### :green[Transformation]")

    # st.markdown("""
    #     The extracted data was written to flat CSV with one row per track. Before loading, the data was
    #     normalized into the relational structure defined by the schema — separating artists, albums, songs,
    #     and genres into their own entities and building the relationships between them.
    #     Genre names were imported as-is from the dataset, which were already consistently lowercase.

    #     During seeding, duplicate relationships were resolved at two levels: duplicate records were tracked
    #     in memory using a `seen` set before insertion, and `INSERT OR IGNORE` was used as a second safeguard at
    #     the database level to prevent constraint violations in the event of any duplicates that slipped through.
    #             """)

    st.markdown("**:green[3 )] &nbsp; SEEDING ORDER**")
    st.divider()
    st.space("xxsmall")

    steps = [
    ("Genres", "no deps"),
    ("Artists", "no deps"),
    ("Albums", "← Artists"),
    ("Songs", "← Albums"),
    ("Song Genres", "← Songs, Genres"),
    ("Album Credits", "← Albums, Artists"),
    ("Song Credits", "← Songs, Artists"),
    ]

    # Code by Claude AI to display seeding order
    with st.container(border=False):
        cols = st.columns(len(steps) * 2 - 1)
        for i, (name, dep) in enumerate(steps):
            with cols[i * 2]:
                st.markdown(f"""
                <div style="text-align:center;">
                    <div style="background:#5de488; color:#0d1116; border-radius:50%;
                                width:35px; height:35px; line-height:35px; margin:0 auto;
                                font-size:16px; font-weight:600;">{i+1}</div>
                    <div style="font-size:16px; font-weight:500; margin-top:6px;">{name}</div>
                    <div style="font-size:14px; color:grey;">{dep}</div>
                </div>
                """, unsafe_allow_html=True)
            if i < len(steps) - 1:
                with cols[i * 2 + 1]:
                    st.markdown("<div style='text-align:center; padding-top:4px; color:grey;'>→</div>",
                                unsafe_allow_html=True)

        st.space("xxsmall")

        with st.container(key="grey_container"):

            col1, col2 = st.columns([0.2,5])

            col1.markdown(":grey[:material/Info:]")

            with col2:
                st.markdown(""" **Design note** <br>
                    :grey[Album titles aren't unique across artists and the source dataset
                            had no album IDs. Adding artist_id to the albums table made
                            (title, artist) the composite key, preventing unrelated albums
                            from merging.]
                            """, unsafe_allow_html=True)
    # st.markdown("""
    #     Tables were seeded in dependency order to satisfy foreign key constraints — parent tables first,
    #     child and relationship tables after. A table can only reference a primary key that already exists,
    #     so the order was:""")

    # st.markdown("""
    #     &nbsp;&nbsp;&nbsp;&nbsp; 1. :green[**Genres**] — no dependencies

    #     &nbsp;&nbsp;&nbsp;&nbsp; 2. :green[**Artists**] — no dependencies

    #     &nbsp;&nbsp;&nbsp;&nbsp; 3. :green[**Albums**] — depends on Artists

    #     &nbsp;&nbsp;&nbsp;&nbsp; 4. :green[**Songs**] — depends on Albums

    #     &nbsp;&nbsp;&nbsp;&nbsp; 5. :green[**Song Genres**] — depends on Songs and Genres

    #     &nbsp;&nbsp;&nbsp;&nbsp; 6. :green[**Album Credits**] — depends on Albums and Artists

    #     &nbsp;&nbsp;&nbsp;&nbsp; 7. :green[**Song Credits**] — depends on Songs and Artists
    #             """)

    # st.markdown("""
    #     One challenge that emerged during the albums seeding step was that album titles are not necessarily
    #     unique — different artists can have albums with the same name, and the source dataset provided no
    #     album identifiers. Without a way to distinguish them, unrelated albums sharing a title would have
    #     been merged into a single record. To resolve this, an artist_id field was incorporated into the albums
    #     table, making the combination of album title and artist the unique identifier for each album. This was
    #     an example of adapting the schema to the limitations of real-world source data.
    #             """)


st.space("small")

st.markdown("#### :green[:material/Data_Object:] Synthetic Data Generation")
col1, col2, col3, col4, col5 = st.columns(5, border=True)

with col1:
    st.metric(label=":grey[:green[:material/Group:] **USERS GENERATED**]", value=500)
with col2:
    st.metric(label=":grey[:green[:material/Globe:] **COUNTRIES**]", value=15)
    st.caption("US ≈ 30%")
with col3:
    st.metric(label=":grey[:green[:material/Star:] **FREE / PREMIUM**]", value="60/40")
    st.caption("% split")
with col4:
    st.metric(label=":grey[:green[:material/Calendar_Today:] **SIGNUP WINDOW**]", value="2 yrs")
    st.caption("capped before today")
with col5:
    st.metric(label=":grey[:green[:material/Play_Arrow:] **MAX STREAMS /  USER**]", value=f"{1000:,}")
    st.caption("heavy listeners")

with st.container(key="grey_container_3"):

    col_a, col_b = st.columns([0.2,5])

    col_a.markdown(":grey[:material/Info:]")

    with col_b:
        st.markdown(""" **Design note** <br>
            :grey[The two-year cap prevents streams from being generated before a
            user's signup date, since the stream model biases toward recent dates.]
                    """, unsafe_allow_html=True)

st.space("xxsmall")

with st.container(border=True):
    st.markdown("##### :green[:material/Account_Circle:] Per-user behavioral profile")
    col1, col2, col3 = st.columns(3, border=True)
    with col1:
        st.markdown("###### :green[:material/Music_Note_2:] Favorite genres")
        st.caption("1-3 randomly selected")
    with col2:
        st.markdown("###### :green[:material/Mic:] Favorite artists")
        st.caption("≥1 per favorite genre")
    with col3:
        st.markdown("###### :green[:material/Schedule:] Listener type")
        st.caption("Day or night window")
    col4, col5, col6 = st.columns(3, border=True)
    with col4:
        st.markdown("###### :green[:material/Skip_Next:] Skip rate")
        st.caption("5–40% per stream")
    with col5:
        st.markdown("###### :green[:material/Repeat:] Replay tendency")
        st.caption("5–35% probability")
    with col6:
        st.markdown("###### :green[:material/Explore:] Exploration rate")
        st.caption("20–70% outside favorites")
    with st.container(border=True):
        st.markdown("###### :green[:material/Leaderboard:] Activity level")
        col1, col2, col3 = st.columns([0.4,3,0.5])
        col1.markdown(":grey[Light]")
        col2.progress(40, ":grey[50 -- 150 streams]")
        col3.markdown(":grey[40%]")
        col1, col2, col3 = st.columns([0.4,3,0.5])
        col1.markdown(":grey[Medium]")
        col2.progress(40, ":grey[150 -- 400 streams]")
        col3.markdown(":grey[40%]")
        col1, col2, col3 = st.columns([0.4,3,0.5])
        col1.markdown(":grey[Heavy]")
        col2.progress(20, ":grey[400 -- 1000 streams]")
        col3.markdown(":grey[20%]")

st.space("xxsmall")

col_a, col_b = st.columns(2, border=True)

with col_a:
    st.markdown("##### :green[:material/Format_List_Numbered:] Song selection priority")
    st.divider()
    st.markdown("""
        :green[1] &nbsp; Replay -- :grey[recent song, p = replay tendency]

        :green[2] &nbsp; Explore -- :grey[ random from full catalog, p = exploration rate]

        :green[3] &nbsp; Favorite artist -- :grey[60% of remaining]

        :green[4] &nbsp; Favorite genre -- :grey[fallback default]
                """)

with col_b:
    st.markdown("##### :green[:material/Timer:] Timestamp behavior")
    st.divider()
    col1, col2, col3 = st.columns([0.8,3,0.5])
    col1.markdown(":grey[Last month]")
    col2.progress(40)
    col3.markdown(":grey[40%]")
    col1, col2, col3 = st.columns([0.8,3,0.5])
    col1.markdown(":grey[Last year]")
    col2.progress(40)
    col3.markdown(":grey[40%]")
    col1, col2, col3 = st.columns([0.8,3,0.5])
    col1.markdown(":grey[Older]")
    col2.progress(20)
    col3.markdown(":grey[20%]")

st.space("xxsmall")

with st.container(border=True):
    st.markdown("##### :green[:material/Favorite:] Liked Song Generation")
    st.divider()
    st.markdown("""
    :grey[Likes are derived from the `candidate_metrics` view, which excludes skipped
    streams — only meaningful listens count toward a user's score.]
                """)
    st.markdown("""
    :grey[`liked_datetime` is set to the user's most recent stream of that song,
    simulating the natural behavior of liking after repeated listens.]
                """)

    st.space("xxsmall")
    st.markdown("**Like probability by engagement score**")
    col1, col2, col3 = st.columns([0.7,3,0.5])
    col1.markdown(":grey[Score 0-1]")
    col2.progress(0)
    col3.markdown(":grey[0%]")
    col1, col2, col3 = st.columns([0.7,3,0.5])
    col1.markdown(":grey[Score 2]")
    col2.progress(40)
    col3.markdown(":grey[40%]")
    col1, col2, col3 = st.columns([0.7,3,0.5])
    col1.markdown(":grey[Score 3]")
    col2.progress(75)
    col3.markdown(":grey[75%]")
    col1, col2, col3 = st.columns([0.7,3,0.5])
    col1.markdown(":grey[Score 4]")
    col2.progress(95)
    col3.markdown(":grey[95%]")
    st.markdown(":grey[**Each point:** &nbsp; +1 if streams ≥3×, &nbsp; +1 if ≥5×, &nbsp; +1 if avg completion ≥60%, &nbsp; +1 if ≥80%]")
# with st.container(border=True):

    # st.markdown("#### :green[User Generation]")

    # st.write("""
    #     500 synthetic users were generated using the Faker library for usernames and probabilistic sampling for
    #     all other attributes.

    #     Country distribution was modeled after real Spotify geographic data, with the US comprising 30% of users
    #     and the remaining 14 countries sharing the rest. Subscription type was assigned with a 60/40 free-to-premium
    #     split, also based on Spotify's reported user distribution.

    #     Signup dates were generated randomly between the platform launch date (January 1, 2020) and two years before
    #     the current date. The two-year cap was intentional — the stream generation model biases toward recent dates,
    #     so capping signup dates ensures no streams are generated before a user's signup date.
    #          """)

    # st.markdown("#### :green[Preference Modeling]")

    # st.write("""
    #     Before generating streams, each user was assigned a behavioral profile to simulate realistic and varied
    #     listening habits. Each profile contains:

    #     * :green[**Favorite genres**] — 1 to 3 randomly selected genres

    #     * :green[**Favorite artists**] — at least 1 artists per favorite genre, drawn from artists who actually have songs in that genre

    #     * :green[**Listener type**] — day or night, determining which hours of the day the user is most active

    #     * :green[**Skip rate**] — between 0.05 and 0.40, controlling how often the user skips songs

    #     * :green[**Replay tendency**] — between 0.05 and 0.35, controlling how often the user replays previously heard songs

    #     * :green[**Exploration rate**] — between 0.20 and 0.70, controlling how often the user streams outside their favorites

    #     * :green[**Activity level**] — light (50–150 streams), medium (150–400), or heavy (400–1000), assigned with weights of 40%, 40%, and 20%

    #     These profiles are not stored in the database — they exist only during stream generation to drive probabilistic behavior.
    #          """)

    # st.markdown("#### :green[Stream Generation]")

    # st.write("""
    #     Each user's streams were generated according to their behavioral profile. For each stream, song selection followed
    #     a priority hierarchy:

    #     1. :green[**Replay**] — if the user has a listening history, they replay a recent song with probability equal to their replay tendency

    #     2. :green[**Exploration**] — with probability equal to their exploration rate, a random song is selected from the full catalog

    #     3. :green[**Favorite artist**] — with 60% probability, a song is selected from one of the user's favorite artists

    #     4. :green[**Favorite genre**] — as the default fallback, a song is selected from one of the user's favorite genres


    #     Stream timestamps were generated with a recency bias — 40% of streams fall within the last month, 40% within the last year,
    #     and 20% are older. Hours were biased toward each user's preferred listening window 70% of the time, with the remaining 30%
    #     drawn from random hours to simulate occasional off-pattern activity.

    #     Skips were simulated by generating `ms_played` values between 5 and 29 seconds with probability equal to the user's
    #     skip rate. Non-skipped streams were assigned a random `ms_played` between 30 seconds and the song's full duration.
    #          """)

    # st.markdown("#### :green[Probabilistic Liked-Song Generation]")
    # st.markdown("""
    #     Liked songs were generated probabilistically based on each user's engagement with the songs they streamed, using the
    #     `candidate_metrics` view as the data source. Skipped streams are excluded from this view, so only meaningful listens were considered.

    #     Each user-song pair was assigned a score of 0 to 4 based on two engagement signals:

    #     * :green[**Stream count**] — +1 if streamed at least 3 times, +1 if streamed at least 5 times

    #     * :green[**Completion rate**] — +1 if average completion rate is at least 60%, +1 if at least 80%

    #     Scores below 2 were assigned a like probability of 0, reflecting that low engagement is unlikely to result in a like.
    #     Scores of 2, 3, and 4 were assigned probabilities of 40%, 75%, and 95% respectively — rewarding deeper engagement with
    #     a higher chance of generating a like. A song with the maximum score was streamed repeatedly and listened to nearly in full,
    #     making it a strong candidate for a liked song.

    #     The `liked_datetime` was set to the user's most recent stream of that song, simulating the natural behavior of liking a song
    #     after repeated listens.
    #             """)

