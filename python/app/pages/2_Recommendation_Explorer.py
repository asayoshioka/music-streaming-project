import streamlit as st
import altair as alt
import pandas as pd
import sqlite3
from utils.user_taste_profiles import get_user_behavior_metrics, get_user_taste_profile
from utils.get_ids_and_maps import get_id_value_map, get_user_ids, get_song_id
from utils.recommendations import (get_recommendations_for_user,
                                   get_recommendations_for_song,
                                   get_recommendation_profile,
                                   get_recommendation_profile_2,
                                   explain_recommendation,
                                   explain_recommendation_2,
                                   get_song_genre)
from utils.queries import (get_song_titles_and_artists,
                           get_similar_user_count,
                           get_song_stats)


DB_PATH = "/workspaces/music-streaming-project/db/music.db"

USERNAME_MAP = get_id_value_map(table="users", value_column="username")

user_ids = get_user_ids()

song_titles_w_artists = get_song_titles_and_artists()

# Generates avatar URL for similar users display -- code from Google AI
def get_initials_avatar(name, size=64, background="random"):
    return f"https://ui-avatars.com/api/?name={name}&size={size}&background={background}&rounded=10&bold=true"

# Adjusted for user profile icon
def get_initials_avatar_2(name, size=64, background="random"):
    return f"https://ui-avatars.com/api/?name={name}&size={size}&background={background}&rounded=true&bold=true"

# Set page title and layout
st.set_page_config(page_title="Music Analytics | Asa",
                   page_icon="🎧", layout="wide")

# TITLE & MODE
title_col, mode_col = st.columns([5,1])
with mode_col:
    st.space("small")
    mode = st.pills("Explore by:", ["User", "Song"], default="User", label_visibility="collapsed")
with title_col:
    st.header("Recommendation Explorer :green[:material/Stars_2:]")


# *** USER MODE ***
if mode == "User":

    # Filter bar for min. score and number of recs
    with st.container(border=True):
        user_col, choice_col, score_col, rec_col = st.columns([0.4,1,2,2])
        with user_col:
            st.markdown("**:grey[:material/Account_circle: &nbsp; User]**")
        with choice_col:
            user_id = st.selectbox("Choose a user:", user_ids, index=4, label_visibility="collapsed")
        with score_col:
            col_1, col_2 = st.columns([1,2.5])
            with col_1:
                st.markdown(":grey[&nbsp; | &nbsp; Min score]")
            with col_2:
                min_score = st.slider("Min score",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.5,
                        label_visibility="collapsed")
        with rec_col:
            col_1, col_2 = st.columns([1,2.5])
            with col_1:
                st.markdown(":grey[&nbsp; | &nbsp; Recs]")
            with col_2:
                max_recs = st.slider("Recs",
                                    min_value=1,
                                    max_value=30,
                                    value=10,
                                    label_visibility="collapsed")

    st.space("small")

    # Get user's username
    username = USERNAME_MAP[user_id]

    # Get user's taste profile
    taste_profile = get_user_taste_profile(user_id)

    # USER'S TOP GENRE(S)

    # Separate user's top genres by commas
    genres = []

    for genre in taste_profile["top_genres"]:
        genres.append(genre["genre"])

    top_genres = ", ".join(genres)

    # USER'S TOP ARTIST(S)

    # Separate user's top artists by commas
    artists = []

    for artist in taste_profile["top_artists"]:
        artists.append(artist["artist"])

    top_artists = ", ".join(artists)

    # USER'S LISTENER TYPE(S)
    listener_types = taste_profile["listener_types"]

    # Separate listener types by commas
    listener_types_str = ", ".join(taste_profile["listener_types"])

    # SIMILAR USERS COUNT USED IN RECOMMENDATION GENERATION
    similar_users  = get_similar_user_count(user_id=user_id)

    # Get recommended songs dataframe w/ columns
    # song_id, Song, Artist, Rec Score, Overlap Strength,
    # Overlap Breadth,Avg Replays, Avg Completion
    df = get_recommendations_for_user(user_id=user_id,
                            min_score=min_score,
                            max_recs=max_recs)

    # Create tuple of recommended song titles (for explanation expander)
    rec_songs = tuple(df["Song"].astype(str))

    # Display selected user (id and username)
    profile_col, user_col = st.columns([1,17])
    with profile_col:
        avatar_url = get_initials_avatar_2(name=username)
        st.image(avatar_url, width=45)
    with user_col:
        st.markdown(f"##### :grey[User {user_id}] <br> {username}", unsafe_allow_html=True)

    # RECOMMENDED SONGS

    if df.empty:
        st.markdown("""No recommendations. Try adjusting the min.
                    recommendation score or number of recommendations.""")
    else:
        # Display key stats
        col1, col2, col3, col4 = st.columns(4, border=True)

        with col1:
            st.metric(label=":grey[:green[:material/Music_Note_2:] Recs]",
                    value=f":green[{len(df.index)}]")

        with col2:
            st.metric(label=":grey[:green[:material/Star:] Avg score]",
                    value=f"{df["Rec Score"].mean():.2f}")

        with col3:
            st.metric(label=":grey[:green[:material/Repeat:] Avg replays]",
                    value=f"{df["Avg Replays"].mean():.1f}")

        with col4:
            st.metric(label=":grey[:green[:material/Group:] Similar users]",
                    value=similar_users)

        # Display recommended songs and user profile
        recs, profile = st.columns([2.5,1], border=True)

        with recs:
            with st.container(height=500, border=False):
                st.markdown("**:grey[:material/List: RECOMMENDED SONGS]**")
                # Iterate through rows w/ itertuples
                for i, song in enumerate(df.itertuples(index=False), start=1):

                    col1, cover, col2, col3, col4 = st.columns([0.5, 1, 3, 4.5, 1.5])

                    with col1:
                        st.markdown(f":grey[{i}]")

                    with cover:
                        avatar_url = get_initials_avatar(name=song.Song)
                        st.image(avatar_url, width=50)

                    with col2:
                        st.markdown(f"""
                                    **{song.Song}** <br>
                                    :grey[{song.Artist}]
                                    """, unsafe_allow_html=True)

                    with col3:
                        st.progress(song[3], text="")

                    with col4:
                        st.markdown(f":grey[{song[3]}]")

                    # Custom CSS to limit space around the divider -- from Google AI
                    st.markdown(
                        """
                        <style>
                        hr {
                            margin-top: -1.6rem !important;
                            margin-bottom: -2.0rem !important;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.divider()

        with profile:
            st.markdown("**:grey[USER PROFILE]**")

            st.markdown(":grey[:material/Album: Top genres]")
            genre_string = ""
            for genre in genres:
                genre_string += f":green-badge[{genre}] "
            st.markdown(genre_string)

            st.markdown(":grey[:material/Artist: Top artists]")
            artist_string = ""
            for artist in artists:
                artist_string += f":blue-badge[{artist}] "
            st.markdown(artist_string)

            st.markdown(":grey[:material/Headphones: Listener Type]")
            type_string = ""
            for type in listener_types:
                type_string += f":violet-badge[{type}] "
            st.markdown(type_string)

        # RECOMMENDATION EXPLANATION
        with st.container(border=True):

            st.markdown("**:grey[:material/Stars_2: RECOMMENDATION EXPLANATION]**")

            # Recommended Song Selection
            song = st.pills("Choose a song:", rec_songs, default=rec_songs[0], label_visibility="collapsed")

            col1, col2 = st.columns([2.1,1], border=True)

            with col1:

                # Display selected song
                st.markdown(f"##### {song}")

                # Get recommendation profile
                rec_profile = get_recommendation_profile(user_id=user_id,
                                                        song=song,
                                                        df=df)

                # Get recommendation explanation
                explanation = explain_recommendation(rec_profile)

                st.markdown(explanation)

            with col2:
                st.markdown("**:grey[SCORE BREAKDOWN]**")

                # Get rec. song data from df
                song_data = df.loc[df["Song"] == song, ["normalized_weighted_overlap",
                                                        "normalized_similar_users",
                                                        "normalized_replays",
                                                        "Avg Completion"]]
                # Convert to tuple
                song_data = tuple(song_data.iloc[0])

                # Multiply by weights
                overlap_strength = song_data[0]*0.45
                overlap_breadth = song_data[1]*0.25
                replay_rate = song_data[2]*0.20
                completion_rate = song_data[3]*0.10

                st.progress(overlap_strength, text=f":grey[Overlap strength] {"\u00A0"*55} **{overlap_strength:.2f}**")
                st.progress(overlap_breadth, text=f":grey[Overlap breadth] {"\u00A0"*56} **{overlap_breadth:.2f}**")
                st.progress(replay_rate, text=f":grey[Replay rate] {"\u00A0"*66} **{replay_rate:.2f}**")
                st.progress(completion_rate, text=f":grey[Completion rate] {"\u00A0"*56} **{completion_rate:.2f}**")

                st.space("small")
                st.divider()

                st.markdown(f":grey[Total] {"\u00A0"*67} :green[**{overlap_strength+overlap_breadth+replay_rate+completion_rate:.2f}**]")

        # Hide dataframe -- use for debugging
        # st.dataframe(df,
        #             hide_index=True,
        #             column_config={
        #                 # hide columns from view,
        #                 "song_id": None,
        #                 "normalized_weighted_overlap": None,
        #                 "normalized_similar_users": None,
        #                 "normalized_replays": None,
        #                 "Song": st.column_config.Column(width=140),
        #                 "Artist": st.column_config.Column(width=140)
        #                 }
        #             )


    # RECOMMENDATION SCORE BREAKDOWN
    with st.expander("**:grey[:material/Grading: Recommendation Score Breakdown]**"):

        # Formula
        st.code("Recommendation Score = 0.45 × Overlap Strength + 0.25 × Overlap Breadth + 0.20 × Replay Rate + 0.10 × Completion Rate", language=None)

        st.write(""":grey[Each song is scored using a weighted combination of four components.
                Overlap Strength, Overlap Breadth, and Replay Rate are each normalized
                to a 0–1 scale relative to the highest value among all candidate songs.]""")

        # Component cards
        components = [
            ("Overlap Strength", "0.45", "How similar the users who streamed a song are to the target "
            "user, weighted by shared songs. A user sharing 18 songs contributes far more than one "
            "sharing only 2. The dominant signal."),
            ("Overlap Breadth", "0.25", "How many distinct similar users streamed the song. A similar "
            "user is anyone who has genuinely engaged with at least one of the same songs as the "
            "target user — at least 2 replays and 50% completion."),
            ("Replay Rate", "0.20", "The average number of times similar users replayed the song. "
            "Rewards tracks that drive repeat engagement."),
            ("Completion Rate", "0.10", "The average share of the song similar users listened to. "
            "Rewards tracks that hold attention through to the end."),
        ]

        for name, weight, description in components:
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f":green[**{name}**]")
                    st.caption(description)
                with col2:
                    st.metric(label="Weight", value=f":green[{weight}]")

        # Engagement filter
        st.markdown("###### ENGAGEMENT FILTER")
        st.write(":grey[Only streams with at least 2 replays and 50% completion are counted when "
                "identifying similar users and candidate songs. This filters out incidental "
                "listens, ensuring recommendations are grounded in genuine engagement.]")

        st.caption("Weights were selected heuristically and could later be tuned experimentally "
                "or learned from user interaction data.")


    # RECOMMENDATION VISUALIZATIONS

    if not df.empty:

        with st.container(border=True):
            # RECOMMENDED SONGS RANKED BY SCORE
            st.markdown("**:grey[:material/Bar_Chart: SCORES BY SONG]**")

            st.space("xsmall")

            # Construct a top recommendation scores dataframe
            df_subset = df[["Song", "Rec Score"]]

            # Create an Altair bar chart to order songs by descending score
            chart = alt.Chart(df_subset).mark_bar(color="#5de488").encode(
                    x=alt.X("Song", sort="-y"), # Sorts x-axis by y-axis values descending
                    y="Rec Score"
                    )

            # Display the bar chart in Streamlit
            st.altair_chart(chart)


# *** SONG MODE ***
if mode == "Song":

    # Filter bar for min. score and number of recs
    with st.container(border=True):
        song_col, choice_col, score_col, rec_col = st.columns([0.5,1.5,2,2])
        with song_col:
            st.markdown("**:grey[:material/Music_Note_2: &nbsp; Song]**")
        with choice_col:
            default_index = song_titles_w_artists.index('"deja vu" by Olivia Rodrigo')
            song_and_artist = st.selectbox("Choose a song:", song_titles_w_artists,
                                           index=default_index,
                                           label_visibility="collapsed")
        with score_col:
            col_1, col_2 = st.columns([1,2.5])
            with col_1:
                st.markdown(":grey[&nbsp; | &nbsp; Min score]")
            with col_2:
                min_score = st.slider("Min score",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.5,
                        label_visibility="collapsed")
        with rec_col:
            col_1, col_2 = st.columns([1,2.5])
            with col_1:
                st.markdown(":grey[&nbsp; | &nbsp; Recs]")
            with col_2:
                max_recs = st.slider("Recs",
                                    min_value=1,
                                    max_value=30,
                                    value=10,
                                    label_visibility="collapsed")

    st.space("small")

    # Split song title and artist
    song_title, artist = song_and_artist.split(" by ")
    # Remove quotes from song_title
    song_title = song_title.replace('"', '')
    # Get song_id
    song_id = get_song_id(song_title=song_title, artist=artist)
    # Get song genre
    song_genre = get_song_genre(song_id=song_id)
    # Get song stats for display
    stats_df = get_song_stats(song_id=song_id)

    # Display selected song
    profile_col, user_col = st.columns([1,17])
    with profile_col:
        avatar_url = get_initials_avatar(name=song_title)
        st.image(avatar_url, width=45)
    with user_col:
        st.markdown(f"##### {song_title} <br> :grey[{artist}]", unsafe_allow_html=True)

    # Get recommended songs dataframe w/ columns
    # song_id, Song, Artist, Rec Score, Shared Users,
    # Avg Replays, Avg Completion
    df = get_recommendations_for_song(song_id=song_id,
                                    min_score=min_score,
                                    limit=max_recs)

    rec_songs = tuple(df["Song"].astype(str))

    if df.empty:
        st.write("No recommendations. Try adjusting the min. " \
                "recommendation score or number of recommendations.")
    else:
        # Display key stats
        col1, col2, col3, col4 = st.columns(4, border=True)

        with col1:
            st.metric(label=":grey[:green[:material/Music_Note_2:] Recs]",
                    value=f":green[{len(df.index)}]")

        with col2:
            st.metric(label=":grey[:green[:material/Star:] Avg score]",
                    value=f"{df["Rec Score"].mean():.2f}")

        with col3:
            st.metric(label=":grey[:green[:material/Repeat:] Avg replays]",
                    value=f"{df["Avg Replays"].mean():.1f}")

        with col4:
            st.metric(label=":grey[:green[:material/Group:] Shared users]",
                    value=f"{stats_df["total_listeners"].iloc[0]}")


        # Display recommended songs and song profile
        recs, profile = st.columns([2.5,1], border=True)

        with recs:
            with st.container(height=500, border=False):
                st.markdown("**:grey[:material/List: RECOMMENDED SONGS]**")
                # Iterate through rows w/ itertuples
                for i, song in enumerate(df.itertuples(index=False), start=1):

                    col1, cover, col2, col3, col4 = st.columns([0.5, 1, 3, 4.5, 1.5])

                    with col1:
                        st.markdown(f":grey[{i}]")

                    with cover:
                        avatar_url = get_initials_avatar(name=song.Song)
                        st.image(avatar_url, width=50)

                    with col2:
                        st.markdown(f"""
                                    **{song.Song}** <br>
                                    :grey[{song.Artist}]
                                    """, unsafe_allow_html=True)

                    with col3:
                        st.progress(song[3], text="")

                    with col4:
                        st.markdown(f":grey[{song[3]}]")

                    # Custom CSS to limit space around the divider -- from Google AI
                    st.markdown(
                        """
                        <style>
                        hr {
                            margin-top: -1.6rem !important;
                            margin-bottom: -2.0rem !important;
                        }
                        </style>
                        """,
                        unsafe_allow_html=True,
                    )

                    st.divider()

        with profile:
            st.markdown("**:grey[SONG PROFILE]**")

            st.markdown(":grey[:material/Album: Genre]")
            st.markdown(f":green-badge[{song_genre}]")

            st.markdown(":grey[:material/Artist: Artist]")
            st.markdown(f":violet-badge[{artist}]")

            st.space("xxsmall")
            st.divider()

            stat_col, val_col = st.columns([3,1])

            with stat_col:
                st.markdown(f""":grey[
                :material/Repeat: &nbsp; Avg replays <br>
                :material/Play_Arrow: &nbsp; Avg completion <br>
                :material/Group: &nbsp; Total listeners]
                            """, unsafe_allow_html=True)
            with val_col:
                st.markdown(f"""
                {stats_df["avg_replays"].iloc[0]:.1f} <br>
                {round(stats_df["avg_completion"].iloc[0] * 100)}% <br>
                {stats_df["total_listeners"].iloc[0]} <br>
                            """, unsafe_allow_html=True)

        # RECOMMENDATION EXPLANATION
        with st.container(border=True):

            st.markdown("**:grey[:material/Stars_2: RECOMMENDATION EXPLANATION]**")

            # Recommended Song Selection
            song = st.pills("Choose a song:", rec_songs, default=rec_songs[0], label_visibility="collapsed")

            col1, col2 = st.columns([2,1], border=True)

            with col1:

                # Display selected song
                st.markdown(f"##### {song}")

                # Get recommendation profile
                rec_profile = get_recommendation_profile_2(song1_id=song_id, song2=song, df=df)

                # Get recommendation explanation
                explanation = explain_recommendation_2(rec_profile)

                st.markdown(explanation)

            with col2:
                st.markdown("**:grey[SCORE BREAKDOWN]**")

                # Get rec. song data from df
                song_data = df.loc[df["Song"] == song, ["normalized_shared",
                                                        "normalized_replays",
                                                        "Avg Completion"]]
                # Convert to tuple
                song_data = tuple(song_data.iloc[0])

                # Multiply by weights
                shared_users = song_data[0]*0.60
                replay_rate = song_data[1]*0.20
                completion_rate = song_data[2]*0.20

                st.progress(shared_users, text=f":grey[Shared users] {"\u00A0"*67} **{shared_users:.2f}**")
                st.progress(replay_rate, text=f":grey[Replay rate] {"\u00A0"*70} **{replay_rate:.2f}**")
                st.progress(completion_rate, text=f":grey[Completion rate] {"\u00A0"*60} **{completion_rate:.2f}**")

                st.space("small")
                st.divider()

                st.markdown(f":grey[Total] {"\u00A0"*70} :green[**{shared_users+replay_rate+completion_rate:.2f}**]")

    # RECOMMENDATION SCORE BREAKDOWN
    with st.expander("**:grey[:material/Grading: Recommendation Score Breakdown]**"):

        # Formula
        st.code("Recommendation Score = 0.6 × Shared Users + 0.2 × Replay Rate + 0.2 × Completion Rate", language=None)

        st.write(":grey[Each song is scored using a weighted combination of three components. "
                "Shared Users and Replay Rate are each normalized to a 0–1 scale relative "
                "to the highest value among all candidate songs.]")

        # Component cards
        components = [
            ("Shared Users", "0.6", "The number of users who streamed both the selected song and the "
            "candidate song. Two songs are considered related when the same listeners tend to stream "
            "both, making this the dominant signal for song similarity."),
            ("Replay Rate", "0.2", "The average number of times those shared users replayed the "
            "candidate song. Rewards tracks that drive repeat engagement."),
            ("Completion Rate", "0.2", "The average share of the candidate song listened to by shared "
            "users. Rewards tracks that hold attention through to the end."),
        ]

        for name, weight, description in components:
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f":green[**{name}**]")
                    st.caption(description)
                with col2:
                    st.metric(label="Weight", value=f":green[{weight}]")


        st.caption("Weights were selected heuristically and could later be tuned experimentally "
                "or learned from user interaction data.")

    if not df.empty:

        with st.container(border=True):
            # RECOMMENDED SONGS RANKED BY SCORE
            st.markdown("**:grey[:material/Bar_Chart: SCORES BY SONG]**")

            # Construct a top recommendation scores dataframe
            df_subset = df[["Song", "Rec Score"]]

            # Create an Altair bar chart to order songs by descending score
            chart = alt.Chart(df_subset).mark_bar(color="#5de488").encode(
                    x=alt.X("Song", sort="-y"), # Sorts x-axis by y-axis values descending
                    y="Rec Score"
                    )

            # Display the bar chart in Streamlit
            st.altair_chart(chart)








