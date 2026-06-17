import streamlit as st

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

tabs = ["Candidate metrics",
        "Affinity scoring",
        "Diversity metrics",
        "Recommendation queries",
        "Collaborative filtering"
        ]

st.header(":green[:material/Code_Blocks:] SQL & Analytics Engineering")

st.write("""
         *:grey[An overview of the SQL views, queries, and scoring systems that power the
         platform's analytics and recommendations.]*
         """)

st.space("xxsmall")

tab1, tab2, tab3, tab4, tab5 = st.tabs(tabs)

# CANDIDATE METRICS
with tab1:

    with st.container(border=True):
        st.markdown(":green[:material/Star:] **Foundation view**")
        st.markdown("""
        :grey[All analytics and recommendation logic builds on this. Each row captures
        a user's aggregate engagement with one song: stream count, total ms played,
        average completion rate, and latest stream timestamp. Skipped streams excluded.]
                    """, unsafe_allow_html=True)

    cm_view = """
    CREATE VIEW candidate_metrics AS
    SELECT user_id,
           song_id,
           COUNT(*) AS total_streams,
           SUM(ms_played) AS total_ms_played,
           AVG(CAST(ms_played AS REAL) / duration_ms) AS completion_rate,
           MAX(start_datetime) AS latest_stream
    FROM streams
    JOIN songs ON streams.song_id = songs.id
    WHERE skipped = 0 -- Exclude skips
    GROUP BY user_id, song_id
    ORDER BY user_id ASC, song_ID ASC;"""

    st.markdown("**:grey[CANDIDATE METRICS VIEW]**")
    st.code(cm_view, language="sql")

    st.space("small")

    col1, col2 = st.columns(2, border=True)

    with col1:
        st.markdown(":green[:material/Circle:] **Why a view, not an inline subquery**")
        st.markdown("""
        :grey[The same aggregation logic is reused across affinity scoring, diversity metrics,
        recommendations, and liked-song generation. A shared view avoids duplicating it
        and keeps all downstream queries consistent.]
                    """)

    with col2:
        st.markdown(":green[:material/Circle:] **Why skips are excluded**")
        st.markdown("""
        :grey[A skip signals the user did not meaningfully engage. Including skipped streams
        would dilute completion rate and stream count signals used downstream — the view is
        an engagement signal, not a play log.]
                    """)

    # st.markdown("""
    # The `candidate_metrics` view is the foundation for most of the analytics and recommendation logic
    # in this project. Each row captures a user's aggregate engagement with a particular song, including
    # their total streams, total milliseconds played, average completion rate, and most recent stream timestamp.

    # Skipped streams are excluded when aggregating these metrics — a skip indicates the user did not meaningfully
    # engage with a song, so including them would dilute the engagement signals used downstream for affinity scoring,
    # diversity metrics, recommendations, and liked-song generation.

    # The view exists as a reusable building block rather than an inline subquery to avoid duplicating complex
    # aggregation logic across multiple queries and views.
    #             """)

# AFFINITY SCORING
with tab2:

    with st.container(border=True):
        st.markdown(":green[:material/Info:] **What these views compute**")
        st.markdown("""
        :grey[The genre and artist affinity views score a user's preference for each genre
        and artist they have streamed, using three engagement metrics:]

        :green-badge[stream share] :green-badge[replay rate] :green-badge[completion rate]
                    """)
        # st.markdown("""
        # :grey[The genre and artist affinity views score a user's preference for each genre and artist they have streamed,
        # using three engagement metrics: stream share, replay rate, and completion rate. Both stream share and replay
        # rate are normalized per user — relative to that user's own maximum — rather than globally. This ensures that
        # a user who streams lightly is scored fairly against a user who streams heavily, since affinity reflects the
        # relative distribution of a user's listening rather than absolute volume.]
        #             """)

    col_a, col_b = st.columns(2, border=True)

    with col_a:
        st.markdown("**:green[:material/Circle:] Score formula**")
        # Display equation in colored box
        st.markdown("""
        <div style="background:#0a1f12;border-left:3px solid #5de488;border-radius:6px;padding:10px 14px;margin-bottom:1rem">
        <span style="font-family:monospace;font-size:14px;color:#b8f5ce">
            0.6 × Stream Share &nbsp;+&nbsp; 0.2 × Replay Rate &nbsp;+&nbsp; 0.2 × Completion Rate
        </span>
        </div>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1.2,3,0.5])
        col1.markdown(":grey[Stream share]")
        col2.progress(60)
        col3.markdown(":grey[60%]")
        col1, col2, col3 = st.columns([1.2,3,0.5])
        col1.markdown(":grey[Replay rate]")
        col2.progress(20)
        col3.markdown(":grey[20%]")
        col1, col2, col3 = st.columns([1.2,3,0.5])
        col1.markdown(":grey[Completion rate]")
        col2.progress(20)
        col3.markdown(":grey[20%]")

    with col_b:
        st.markdown("**:green[:material/Circle:] Normalization approach**")
        st.markdown("""
        :grey[Stream share and replay rate are normalized per user —
        relative to that user's own maximum — not globally.]
                    """)
        st.markdown("""
        :grey[This means a light listener and a heavy listener are scored
        fairly against themselves. Affinity reflects the *relative distribution*
        of a user's listening, not absolute volume.]
                    """)

    st.space("xxsmall")

    st.markdown("###### :grey[GENRE AFFINITY VIEW]")

    genre_view = """
    CREATE VIEW user_genre_affinity AS
    WITH
        user_streamed_genres AS (
            -- Note: Each song in the database currently maps to
            -- exactly one genre, making this JOIN clause valid.
            SELECT user_id,
                   sg.genre_id,
                   SUM(total_streams) AS total_streams,
                   COUNT(DISTINCT cm.song_id) AS distinct_songs,
                   AVG(completion_rate) AS avg_completion_rate,
                   CAST(SUM(total_streams) AS REAL) /
                       COUNT(DISTINCT cm.song_id) AS avg_streams_per_song
            FROM candidate_metrics cm
            JOIN song_genres sg ON cm.song_id = sg.song_id
            GROUP BY user_id, sg.genre_id
    ),
        max_metrics AS (
            SELECT user_id,
                   MAX(total_streams) AS max_total_streams,
                   MAX(avg_streams_per_song) AS max_avg_streams_per_song
            FROM user_streamed_genres
            GROUP BY user_id
    ),
        normalized_metrics AS (
            SELECT usg.user_id,
                   genre_id,
                   CAST(total_streams AS REAL) /
                       max_total_streams AS normalized_streams,
                   CAST(avg_streams_per_song AS REAL) /
                       max_avg_streams_per_song AS normalized_replays,
                   avg_completion_rate
            FROM user_streamed_genres usg
            JOIN max_metrics mm ON usg.user_id = mm.user_id
    )
    SELECT user_id,
           genre_id,
           genres.name AS genre,
           normalized_streams,
           normalized_replays,
           avg_completion_rate,
           (0.6 * normalized_streams +
               0.2 * normalized_replays +
               0.2 * avg_completion_rate) AS affinity_score
    FROM normalized_metrics nm
    JOIN genres ON nm.genre_id = genres.id
    ORDER BY user_id ASC, affinity_score DESC;"""

    st.code(genre_view, language="sql")

    st.space("xxsmall")

    st.markdown("###### :grey[ARTIST AFFINITY VIEW]")

    artist_view = """
    CREATE VIEW user_artist_affinity AS
    WITH
        user_streamed_artists AS (
            -- Note: Each song in the database currently maps to
            -- exactly one artist, making this JOIN clause valid.
            SELECT user_id,
                   sc.artist_id,
                   SUM(total_streams) AS total_streams,
                   COUNT(DISTINCT cm.song_id) AS distinct_songs,
                   AVG(completion_rate) AS avg_completion_rate,
                   CAST(SUM(total_streams) AS REAL) /
                       COUNT(DISTINCT cm.song_id) AS avg_streams_per_song
            FROM candidate_metrics cm
            JOIN song_credits sc ON cm.song_id = sc.song_id
            GROUP BY user_id, sc.artist_id
    ),
        max_metrics AS (
            SELECT user_id,
                   MAX(total_streams) AS max_total_streams,
                   MAX(avg_streams_per_song) AS max_avg_streams_per_song
            FROM user_streamed_artists
            GROUP BY user_id
    ),
        normalized_metrics AS (
            SELECT usa.user_id,
                   artist_id,
                   CAST(total_streams AS REAL) /
                       max_total_streams AS normalized_streams,
                   CAST(avg_streams_per_song AS REAL) /
                       max_avg_streams_per_song AS normalized_replays,
                   avg_completion_rate
            FROM user_streamed_artists usa
            JOIN max_metrics mm ON usa.user_id = mm.user_id
    )
    SELECT user_id,
           artist_id,
           artists.name AS artist,
           normalized_streams,
           normalized_replays,
           avg_completion_rate,
           (0.6 * normalized_streams +
               0.2 * normalized_replays +
               0.2 * avg_completion_rate) AS affinity_score
    FROM normalized_metrics nm
    JOIN artists ON nm.artist_id = artists.id
    ORDER BY user_id ASC, affinity_score DESC;"""

    st.code(artist_view, language="sql")


# Diversity metrics
with tab3:

    with st.container(border=True):
        st.markdown(":green[:material/Info:] **What this view computes**")
        st.markdown("""
        :grey[A diversity score for each user using the Simpson Diversity Index, plus their dominant genre share.
        Both metrics appear together because they tell complementary stories: the score captures how evenly
        listening is distributed; the share gives a direct measure of how concentrated it is.]
                    """)

    diversity_view = """
    CREATE VIEW user_diversity_metrics AS
    WITH
        total_streams AS (
            SELECT user_id,
                   SUM(total_streams) AS total_streams,
                   COUNT(DISTINCT genre_id) AS distinct_genres
            FROM candidate_metrics cm
            JOIN song_genres sg ON cm.song_id = sg.song_id
            GROUP BY user_id
        ),
        genre_streams AS (
            SELECT user_id,
                   genre_id,
                   SUM(total_streams) AS genre_streams
            FROM candidate_metrics cm
            JOIN song_genres sg ON cm.song_id = sg.song_id
            GROUP BY user_id, genre_id
        ),
        genre_proportions AS (
            SELECT gs.user_id,
                   genre_id,
                   CAST(genre_streams AS REAL) /
                       ts.total_streams AS genre_proportion
            FROM genre_streams gs
            JOIN total_streams ts ON gs.user_id = ts.user_id
        ),
        max_genre_proportions AS (
            SELECT user_id,
                   MAX(genre_proportion) AS dominant_genre_share
            FROM genre_proportions
            GROUP BY user_id
        ),
        diversity_score AS (
            SELECT user_id,
                   (1 - SUM(genre_proportion * genre_proportion))
                       AS diversity_score
            FROM genre_proportions
            GROUP BY user_id
        )
    SELECT ts.user_id,
           ts.total_streams,
           ts.distinct_genres,
           ds.diversity_score,
           mgp.dominant_genre_share
    FROM total_streams ts
    JOIN diversity_score ds ON ts.user_id = ds.user_id
    JOIN max_genre_proportions mgp ON ds.user_id = mgp.user_id;"""

    st.markdown(":grey[**DIVERSITY METRICS VIEW**]")
    st.code(diversity_view, language="sql")

    st.space("xxsmall")

    st.markdown(":grey[**DIVERSITY SCORE BREAKDOWN**]")

    # with st.container(border=True):
    #     st.markdown("""
    #     :grey[The diversity metrics view computes a diversity score for each user using the Simpson Diversity Index,
    #     which accounts for both the number of genres a user streams and how evenly streams are distributed among
    #     them. A user who streams many genres but heavily favors one will score lower than a user whose streams
    #     are spread more evenly.]

    #     :grey[The view also exposes each user's dominant genre share — the proportion of their
    #     total streams belonging to their most-streamed genre — which complements the diversity score by providing
    #     a direct measure of genre concentration.]
    #                 """)

    # Diversity Score Breakdown -- custom css by Claude
    with st.container(border=True):
        st.markdown("##### Diversity Score $= 1 − \\sum (p_i^2)$")
        st.markdown("""
        :grey[where $p_i$ is each genre's share of the user's total streams. Squaring penalizes dominance —
        a genre at 80% contributes 0.64 to the sum, one at 20% contributes only 0.04. Subtracting
        from 1 flips the scale so higher scores mean greater diversity.]
                   """)

    st.markdown("""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-top:.75rem">

    <!-- User A -->
    <div style="background:var(--background-color);border:1px solid #383f41;border-radius:8px;padding:.75rem .875rem">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.625rem">
        <span style="font-size:16px;font-weight:500">User A</span>
        <span style="font-size:15px;padding:2px 8px;border-radius:999px;background:#2a0d0d;color:#e05555;border:1px solid #4a1a1a">Score ≈ 0.18 · Low</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
        <span style="font-size:15px;color:#6b7280;width:52px">Rock</span>
        <div style="flex:1;height:6px;background:#262730;border-radius:3px">
        <div style="width:90%;height:6px;background:#e05555;border-radius:3px"></div>
        </div>
        <span style="font-size:15px;color:#6b7280;width:28px;text-align:right">90%</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
        <span style="font-size:15px;color:#6b7280;width:52px">Pop</span>
        <div style="flex:1;height:6px;background:#262730;border-radius:3px">
        <div style="width:10%;height:6px;background:#e05555;opacity:.5;border-radius:3px"></div>
        </div>
        <span style="font-size:15px;color:#6b7280;width:28px;text-align:right">10%</span>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:.625rem;padding-top:.625rem;border-top:0.5px solid #2a2a2a">
        <span style="font-size:15px;color:#6b7280">Σ(p²) penalty</span>
        <span style="font-size:16px;font-weight:500;font-family:monospace">0.90² + 0.10² = 0.82</span>
    </div>
    </div>

    <!-- User B -->
    <div style="background:var(--background-color);border:1px solid #383f41;border-radius:8px;padding:.75rem .875rem">
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:.625rem">
        <span style="font-size:16px;font-weight:500">User B</span>
        <span style="font-size:15px;padding:2px 8px;border-radius:999px;background:#0d2b1a;color:#5de488;border:1px solid #1e4a2e">Score = 0.75 · High</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
        <span style="font-size:15px;color:#6b7280;width:52px">Rock</span>
        <div style="flex:1;height:6px;background:#262730;border-radius:3px">
        <div style="width:25%;height:6px;background:#5de488;border-radius:3px"></div>
        </div>
        <span style="font-size:15px;color:#6b7280;width:28px;text-align:right">25%</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
        <span style="font-size:15px;color:#6b7280;width:52px">Pop</span>
        <div style="flex:1;height:6px;background:#262730;border-radius:3px">
        <div style="width:25%;height:6px;background:#7f77dd;border-radius:3px"></div>
        </div>
        <span style="font-size:15px;color:#6b7280;width:28px;text-align:right">25%</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
        <span style="font-size:15px;color:#6b7280;width:52px">Hip-Hop</span>
        <div style="flex:1;height:6px;background:#262730;border-radius:3px">
        <div style="width:25%;height:6px;background:#ef9f27;border-radius:3px"></div>
        </div>
        <span style="font-size:15px;color:#6b7280;width:28px;text-align:right">25%</span>
    </div>
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:5px">
        <span style="font-size:15px;color:#6b7280;width:52px">Jazz</span>
        <div style="flex:1;height:6px;background:#262730;border-radius:3px">
        <div style="width:25%;height:6px;background:#d4537e;border-radius:3px"></div>
        </div>
        <span style="font-size:15px;color:#6b7280;width:28px;text-align:right">25%</span>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:.625rem;padding-top:.625rem;border-top:0.5px solid #2a2a2a">
        <span style="font-size:15px;color:#6b7280">Σ(p²) penalty</span>
        <span style="font-size:16px;font-weight:500;font-family:monospace">4 × 0.25² = 0.25</span>
    </div>
    </div>

    </div>
    """, unsafe_allow_html=True)

    st.space("xxsmall")

    with st.container(border=True):
        st.markdown(":green[:material/Circle:] **Dominant genre share**")
        st.markdown("""
        :grey[The view also exposes each user's dominant genre share — the proportion of total streams
        belonging to their most-streamed genre. This complements the diversity score by providing a direct
        measure of concentration without needing to interpret the full distribution.]
                    """)

    # Diversity Score Breakdown (Replaced above)
    # with st.expander(":green[Diversity Score Breakdown]"):
    #     # Diversity Score
    #     st.subheader(":green[Diversity Score]")
    #     st.markdown("""
    #             ##### Diversity Score $= 1 − \\sum (p_i^2)$

    #             where $p_i$ is the proportion of a user's total streams belonging to genre $i$.\n
    #             * Squaring each genre proportion penalizes dominance -- a genre that accounts for 80%
    #             of streams contributes 0.64 to the sum, while one that accounts for 20% contributes only 0.04.
    #             Subtracting from 1 flips the scale so that higher scores reflect greater diversity.\n
    #             * A user whose streams are spread evenly across many genres will have small proportions
    #             that sum to a low value, yielding a score close to 1. A user who streams almost exclusively
    #             one genre will have one proportion close to 1, pushing the score close to 0.
    #             """)
    #     st.subheader(":green[Example:]")
    #     st.write("""
    #             * :green[User A]: &emsp; 90% Rock, 10% Pop &emsp; &emsp; &emsp; &emsp; &emsp; &emsp; &emsp;
    #                             &emsp; &ensp; &emsp; → &emsp; Diversity ≈ low
    #             * :violet[User B]: &emsp; 25% Rock, 25% Pop, 25% Hip-Hop, 25% Jazz &emsp; → &emsp; Diversity ≈ high
    #             """)


# RECOMMENDATION QUERIES
with tab4:

    user_rec_query = """
    WITH
        user_streamed_songs AS (
            SELECT song_id, total_streams, completion_rate
            FROM candidate_metrics
            WHERE user_id = {user_id} AND
            -- Filter out streams with low engagement
                  total_streams >= 2 AND
                  completion_rate >= 0.5
    ),
        cohort_with_shared_streamed_songs AS (
            SELECT user_id, song_id, total_streams, completion_rate
            FROM candidate_metrics
            WHERE user_id != {user_id} AND
                  song_id IN (
                      SELECT song_id
                      FROM user_streamed_songs
                   ) AND
                   -- Filter out streams with low engagement
                   total_streams >= 2 AND
                   completion_rate >= 0.5
    ),
        similar_users AS (
            SELECT user_id,
                   COUNT(*) AS overlap -- measures user's similarity strength
            FROM cohort_with_shared_streamed_songs
            GROUP BY user_id
    ),
        similar_users_streams AS (
            SELECT cm.user_id,
                   cm.song_id,
                   cm.total_streams,
                   cm.completion_rate,
                   su.overlap
            FROM candidate_metrics cm
            JOIN similar_users su ON cm.user_id = su.user_id
            WHERE cm.user_id != {user_id} AND
                  -- Filter out streams with low engagement
                  total_streams >= 2 AND
                  completion_rate >= 0.5
    ),
        similar_users_streams_metrics AS (
            SELECT song_id,
                   -- number of similar users who streamed a song:
                   COUNT(DISTINCT user_id) AS similar_users,
                   -- avg replays per similar user of a song:
                   AVG(total_streams) AS avg_replays,
                   -- avg completion rate per similar user of a song:
                   AVG(completion_rate) AS avg_completion_rate,
                   -- total number of overlap points of a song:
                   SUM(overlap) AS weighted_overlap
            FROM similar_users_streams
            GROUP BY song_id
    ),
        normalized_metrics AS (
            SELECT song_id,
                   similar_users,
                   weighted_overlap,
                   avg_replays,
                   avg_completion_rate,
                   CAST(similar_users AS REAL) / (
                       SELECT MAX(similar_users)
                       FROM similar_users_streams_metrics
                   ) AS normalized_similar_users,
                   CAST(avg_replays AS REAL) / (
                       SELECT MAX(avg_replays)
                       FROM similar_users_streams_metrics
                   ) AS normalized_replays,
                   CAST(weighted_overlap AS REAL) / (
                       SELECT MAX(weighted_overlap)
                       FROM similar_users_streams_metrics
                   ) AS normalized_weighted_overlap
            FROM similar_users_streams_metrics
    ),
        recommended_songs AS (
            SELECT song_id
            FROM similar_users_streams
            EXCEPT
            SELECT song_id
            FROM user_streamed_songs
    )
    SELECT  rs.song_id,
            songs.name AS "Song",
            artists.name AS "Artist",
            ROUND(
                (0.45 * normalized_weighted_overlap +
                 0.25 * normalized_similar_users +
                 0.20 * normalized_replays +
                 0.10 * avg_completion_rate), 2) AS "Rec Score",
            weighted_overlap AS "Overlap Strength",
            similar_users AS "Overlap Breadth",
            ROUND(avg_replays, 1) AS "Avg Replays",
            ROUND(avg_completion_rate, 2) AS "Avg Completion"
    FROM recommended_songs rs
    JOIN songs ON rs.song_id = songs.id
    JOIN song_credits sc ON songs.id = sc.song_id
    JOIN artists ON sc.artist_id = artists.id
    JOIN normalized_metrics nm ON songs.id = nm.song_id
    WHERE "Rec Score" >= {min_score}
    ORDER BY "Rec Score" DESC
    LIMIT {max_recs};"""

    song_rec_query = """
    WITH
        cohort_who_streamed_song AS (
            SELECT user_id
            FROM candidate_metrics
            WHERE song_id = {song_id}
    ),
        cohort_other_streamed_songs AS (
            SELECT song_id, total_streams, completion_rate
            FROM candidate_metrics
            WHERE user_id IN (
                      SELECT user_id
                      FROM cohort_who_streamed_song
                  ) AND
                  -- Exclude the original shared streamed song
                  song_id != {song_id}
    ),
        cohort_shared_streamed_songs AS (
            SELECT song_id,
                   COUNT(*) AS shared_users,
                   AVG(total_streams) AS avg_streams_per_user,
                   AVG(completion_rate) AS avg_completion_rate
            FROM cohort_other_streamed_songs
            GROUP BY song_id
    ),
        normalized_metrics AS (
            SELECT song_id,
                   shared_users,
                   avg_streams_per_user,
                   CAST(shared_users AS REAL) / (
                       SELECT MAX(shared_users)
                       FROM cohort_shared_streamed_songs
                       ) AS normalized_shared,
                   CAST(avg_streams_per_user AS REAL) / (
                       SELECT MAX(avg_streams_per_user)
                       FROM cohort_shared_streamed_songs
                       ) AS normalized_replays,
                   avg_completion_rate
            FROM cohort_shared_streamed_songs
    )
    SELECT nm.song_id,
           songs.name AS "Song",
           artists.name AS "Artist",
           ROUND((0.6 * normalized_shared +
                  0.2 * normalized_replays +
                  0.2 * avg_completion_rate), 2) AS "Rec Score",
           shared_users AS "Shared Users",
           ROUND(avg_streams_per_user, 1) "Avg Replays",
           ROUND(avg_completion_rate, 2) "Avg Completion Rate"
    FROM normalized_metrics nm
    JOIN songs ON nm.song_id = songs.id
    JOIN song_credits sc ON songs.id=sc.song_id
    JOIN artists ON sc.artist_id=artists.id
    WHERE "Rec Score" >= {min_score}
    ORDER BY "Rec Score" DESC
    LIMIT {max_recs};"""

    option = st.pills(label="", options=["User-based", "Song-based"],
                      default="User-based",
                      label_visibility="collapsed")

    if option == "User-based":
        st.markdown("###### :grey[USER-BASED RECOMMENDATIONS]")
        st.code(user_rec_query, language="sql")
        st.space("xxsmall")
        with st.container(border=True):
            st.markdown("**:green[:material/Circle:] Score formula**")
            st.divider()
            st.markdown("""
            <div style="background:#0a1f12;border-left:3px solid #5de488;border-radius:6px;padding:10px 14px;margin-bottom:1rem">
            <span style="font-family:monospace;font-size:14px;color:#b8f5ce">
                0.45 × Overlap Strength &nbsp;+&nbsp; 0.25 × Overlap Breadth &nbsp;+&nbsp; 0.20 × Replay Rate &nbsp;+&nbsp; 0.10 × Completion Rate
            </span>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1.2,3,0.5])
            col1.markdown(":grey[Overlap strength]")
            col2.progress(45)
            col3.markdown(":grey[45%]")
            col1, col2, col3 = st.columns([1.2,3,0.5])
            col1.markdown(":grey[Overlap breadth]")
            col2.progress(25)
            col3.markdown(":grey[25%]")
            col1, col2, col3 = st.columns([1.2,3,0.5])
            col1.markdown(":grey[Replay rate]")
            col2.progress(20)
            col3.markdown(":grey[20%]")
            col1, col2, col3 = st.columns([1.2,3,0.5])
            col1.markdown(":grey[Completion rate]")
            col2.progress(10)
            col3.markdown(":grey[10%]")

            st.divider()

            st.markdown("""
            :grey[Similar users are identified by shared songs with genuine engagement — minimum 2 streams and 50% completion.
            Overlap is split into two components deliberately: breadth counts how many similar users streamed a song;
            strength weights that count by how similar each user is to the target. A song streamed by many loosely similar
            users can score lower than one streamed by fewer highly similar users.]
                        """)

            # st.markdown("""
            # :grey[The user-based recommendation uses weighted collaborative filtering. Given a target user, a cohort of
            # similar users is identified by finding users who have genuinely engaged with at least one of the same
            # songs (minimum 2 streams and 50% completion rate). All songs streamed by those similar users — excluding
            # songs the target user has already streamed — are then gathered as the candidate pool. Candidate songs are
            # then ranked using four components:
            # overlap strength, overlap breadth, replay rate, and completion rate. Separating overlap into two components
            # — the number of similar users who streamed a song, and how similar those users are to the target user — captures
            # both the breadth and strength of the collaborative signal.]
            #             """)

    if option == "Song-based":
        st.markdown("###### :grey[SONG-BASED RECOMMENDATIONS]")
        st.code(song_rec_query, language="sql")
        st.space("xxsmall")
        with st.container(border=True):
            st.markdown("**:green[:material/Circle:] Score formula**")
            st.divider()
            st.markdown("""
            <div style="background:#0a1f12;border-left:3px solid #5de488;border-radius:6px;padding:10px 14px;margin-bottom:1rem">
            <span style="font-family:monospace;font-size:14px;color:#b8f5ce">
                0.6 × Shared Users &nbsp;+&nbsp; 0.2 × Replay Rate &nbsp;+&nbsp; 0.2 × Completion Rate
            </span>
            </div>
            """, unsafe_allow_html=True)
            col1, col2, col3 = st.columns([1.2,3,0.5])
            col1.markdown(":grey[Shared users]")
            col2.progress(60)
            col3.markdown(":grey[60%]")
            col1, col2, col3 = st.columns([1.2,3,0.5])
            col1.markdown(":grey[Replay rate]")
            col2.progress(20)
            col3.markdown(":grey[20%]")
            col1, col2, col3 = st.columns([1.2,3,0.5])
            col1.markdown(":grey[Completion rate]")
            col2.progress(20)
            col3.markdown(":grey[20%]")
            st.divider()
            st.markdown("""
            :grey[Given a seed song, the candidate pool is all other songs streamed by users who also streamed it.
            No overlap strength component is needed — there is no user profile to compare against, so similarity
            is defined entirely by shared listeners. Three components are sufficient to capture the signal.]
                        """)
            # st.markdown("""
            # :grey[The song-based recommendation uses a simpler cohort overlap approach. Given a song, a cohort of users
            # who streamed it is identified, and all other songs streamed by those users — excluding the selected
            # song itself — are gathered as the candidate pool. Candidate songs are then ranked by how many of those
            # users also streamed them, alongside replay rate and completion rate. A separate overlap strength component
            # isn't needed here because there is no user profile to compare against — similarity is defined entirely by
            # shared listeners rather than user-to-user proximity. Three components are sufficient to capture the signal.]
            #             """)
    # st.markdown(":grey[Two recommendation approaches were implemented, each suited to a different context.]")


with tab5:
    st.markdown(":grey[**COLLABORATIVE FILTERING -- ENGINEERING DECISIONS**]")

    col1, col2, col3 = st.columns(3, border=True)

    with col1:
        st.markdown(":green-badge[Engagement filter]")
        st.markdown("**Min 2 streams + 50% completion**")
        st.markdown("""
        :grey[Applied when identifying similar users and candidate songs.
        Prevents incidental or low-quality streams from influencing recommendations.]
                    """)

    with col2:
        st.markdown(":green-badge[Normalization scope]")
        st.markdown("**Normalization before score filter**")
        st.markdown("""
        :grey[Metrics normalized against the full candidate pool before the minimum score
        threshold is applied — reference point stays stable and isn't shaped by which songs pass.]
                    """)

    with col3:
        st.markdown(":green-badge[Overlap signal]")
        st.markdown("**Strength vs breadth separated**")
        st.markdown("""
        :grey[User-based query splits overlap into two weighted components. Breadth = how many similar
        users streamed a song. Strength = how similar those users are to the target.]
                    """)

    # st.markdown("""
    # A few design decisions are worth noting explicitly:

    # * :green[**Engagement filter**] — only streams with at least 2 replays and a 50% completion rate are counted when
    # identifying similar users and candidate songs. This prevents incidental or low-quality streams from influencing recommendations.

    # * :green[**Normalization scope**] — metrics are normalized against the full candidate pool before the minimum score filter is
    # applied. This means the normalization reference point is stable and not influenced by which songs happen to pass the threshold,
    # making scores consistent and comparable.

    # * :green[**Overlap strength vs breadth**] — in the user-based query, these are deliberately separated into two weighted
    # components rather than combined, because they capture different things: breadth measures how many similar users streamed a song,
    # while strength rewards songs streamed by users who are most similar to the target user.
    #             """)
