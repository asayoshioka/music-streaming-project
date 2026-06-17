import streamlit as st
import pandas as pd
from utils.get_ids_and_maps import get_id_value_map, get_user_ids
from utils.user_similarity import get_similar_users
from utils.user_taste_profiles import get_user_taste_profile, get_user_behavior_metrics
from utils.queries import get_shared_songs
from utils.styles import create_ombre_badge

DB_PATH = "/workspaces/music-streaming-project/db/music.db"

USERNAME_MAP = get_id_value_map(table="users", value_column="username")

# Generates avatar URL for similar users display -- code from Google AI
def get_initials_avatar(name, size=64, background="random"):
    return f"https://ui-avatars.com/api/?name={name}&size={size}&background={background}&rounded=true&bold=true"

# For initials w/ rounded square icons
def get_initials_avatar_2(name, size=64, background="random"):
    return f"https://ui-avatars.com/api/?name={name}&size={size}&background={background}&rounded=20&bold=true"

# Generates custom pill component w/ HTML & CSS -- code from Google AI
def custom_pill(label, bg_color, text_color, font_size=16, border_radius=20):
    pill_html = f"""
    <span style="
        background-color: {bg_color};
        color: {text_color};
        padding: 8px 16px;
        font-size: {font_size}px;
        border-radius: {border_radius}px;
        font-weight: bold;
        display: inline-block;
        margin: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        {label}
    </span>
    """
    st.markdown(pill_html, unsafe_allow_html=True)

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

user_ids = get_user_ids()

# Set page title and layout
st.set_page_config(page_title="Music Analytics | Asa",
                   page_icon="🎧", layout="wide")

# Add a header
st.header("User Similarity Explorer :green[:material/Group:] ")

# Filter bar for user selection and min score
with st.container(border=True):
    user_col, choice_col, score_col= st.columns([0.3,1.5,2])
    with user_col:
        st.markdown("**:grey[:material/Account_circle: &nbsp; User]**")
    with choice_col:
        user_id = st.selectbox("Choose a user:", user_ids, index=4, label_visibility="collapsed")
    with score_col:
        col_1, col_2 = st.columns([0.7,2.5])
        with col_1:
            st.markdown(":grey[&nbsp; | &nbsp; Min score]")
        with col_2:
            min_score = st.slider("Min score",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.5,
                    label_visibility="collapsed")

st.space("xxsmall")

# Get user's username
username = USERNAME_MAP[user_id]

# Header -- display selected user
profile, user, result = st.columns([1,13, 4])
with profile:
    avatar_url = get_initials_avatar(name=username, background="5de488")
    profile.image(avatar_url, width=50)
user.markdown(f"##### :grey[User {user_id}] <br> :green[{username}]", unsafe_allow_html=True)


# Get similar users dataframe with columns
# "user_id","Username", "Shared Songs", "Avg Replays",
# "Avg Completion", "normalized_shared_songs", "normalized_replays",
# "Similarity Score"
df = get_similar_users(user_id=user_id, min_score=min_score)

# Create tuple of similar user's usernames (for explanation expander)
similar_users = tuple(df["Username"].astype(str))


# SIMILAR USERS DISPLAY

if df.empty:
    st.write("No similar users. Try adjusting the min. recommendation score.")

else:
    with result:
        st.space("small")
        st.markdown(f":grey[SIMILAR USERS -- {len(df.index)} RESULTS]")

    # Adjust container height for varying similar user counts
    if len(df.index) == 1:
        height = 143
    elif len(df.index) == 2:
        height = 267
    else:
        height = 395

    # Iterate using itertuples to generate cards for each user
    with st.container(height=height):

        for user in df.itertuples(index=False):

            with st.container(border=True):

                col0, col1, col2, col3, col4, col5, col6 = st.columns([0.5, 0.1, 1, 1.5, 1.5, 0.5, 1])

                # Avatar initials
                with col0:
                    avatar_url = get_initials_avatar(name=user.Username)
                    st.image(avatar_url, width=50)

                # Username and shared songs
                with col2:
                    st.markdown(f"""**{user.Username}** <br>
                                :grey[Shared songs] <br>
                                {user[2]} <br>
                                 """,
                                 unsafe_allow_html=True)

                # Avg replays
                with col3:
                    st.markdown(f""" &nbsp; <br>
                                :grey[Replay (shared songs)] <br>
                                {user[3]} <br>
                                 """,
                                 unsafe_allow_html=True)

                # Avg completion rate
                with col4:
                    st.markdown(f"""&nbsp; <br>
                                :grey[Completion (shared songs)] <br>
                                {round(user[4]*100)}% <br>
                                 """,
                                 unsafe_allow_html=True)

                # Similarity score
                # Pill colors:
                # Green -- bg: #183828, text: ##5de488
                # Violet -- bg: #2a2145, text: #b37eff
                # Grey -- bg: #242831, text: #a5a6a9
                with col6:
                    st.space("xxsmall")
                    if user[7] >= 0.65:
                        custom_pill(f"{user[7]}", bg_color="#183828", text_color="#5de488")
                    elif user[7] >= 0.5:
                        custom_pill(f"{user[7]}", bg_color="#2a2145", text_color="#b37eff")
                    else:
                        custom_pill(f"{user[7]}", bg_color="#242831", text_color="#a5a6a9")

    # Removed dataframe (initially displayed )
    # st.dataframe(df,
    #              hide_index=True,
    #              column_config={
    #              # Hide certain columns
    #              "user_id": None,
    #              "normalized_shared_songs": None,
    #              "normalized_replays": None
    #              }
    #             )

    st.space("small")

    # SHARED TASTE BREAKDOWN

    # Similar User Selection
    similar_user = st.selectbox("Choose a user:", similar_users)

    with st.container(border=True):

        # Note: 1 = target user, 2 = similar user

        # Get similar user's id
        similar_user_id = int(df.loc[df["Username"] == similar_user, "user_id"].iloc[0])
        # Get target user's taste profile
        target_user_profile = get_user_taste_profile(user_id=user_id)
        # Get similar user's tase profile
        similar_user_profile = get_user_taste_profile(user_id=similar_user_id)

        # Get user's similarity score
        similarity_score = float(df.loc[df["Username"] == similar_user, "Similarity Score"].iloc[0])

        # Get top genres for both users
        top_genres_1 =  []
        for genre in target_user_profile["top_genres"]:
            top_genres_1.append(genre["genre"])

        top_genres_2 =  []
        for genre in similar_user_profile["top_genres"]:
            top_genres_2.append(genre["genre"])

        shared_genres = list(set(top_genres_1) & set(top_genres_2))
        shared_genres_str = ""
        for genre in shared_genres:
            shared_genres_str += f":blue-badge[{genre}] "

        # Get top artists
        top_artists_1 =  []
        for artist in target_user_profile["top_artists"]:
            top_artists_1.append(artist["artist"])

        top_artists_2 =  []
        for artist in similar_user_profile["top_artists"]:
            top_artists_2.append(artist["artist"])

        shared_artists = list(set(top_artists_1) & set(top_artists_2))
        shared_artists_str = ""
        for artist in shared_artists:
            shared_artists_str += f":blue-badge[{artist}] "

        # Get listener types
        types_1 = target_user_profile["listener_types"]
        types_2 = similar_user_profile["listener_types"]

        shared_types = list(set(types_1) & set(types_2))
        shared_types_str = ""
        for type in shared_types:
            shared_types_str += f":blue-badge[{type}] "

        listener_types_1 = ", ".join(types_1)
        listener_types_2 = ", ".join(types_2)

        # Get shared songs dataframe
        df = get_shared_songs(user_1=user_id, user_2=similar_user_id)

        # Get number of shared songs
        shared_song_count = len(df.index)

        # Shared Taste Summary
        st.markdown("**:grey[SHARED TASTE SUMMARY]**")

        col1, col2, col3, col4 = st.columns(4, border=True)

        col1.metric(label=":grey[:material/Music_Note_2: Shared songs]", value=f"{shared_song_count}")
        col2.metric(label=":grey[:material/Album: Shared genres]", value=f"{len(shared_genres)}")
        col3.metric(label=":grey[:material/Mic: Shared artists]", value=f"{len(shared_artists)}")
        col4.metric(label=":grey[:material/Star: Similarity score]", value=f":green[{similarity_score}]")

        st.space("xxsmall")

        st.markdown("##### :green[:material/Group:] Profile Comparison")

        col1, col2 = st.columns(2, border=True)

        # TARGET USER
        with col1:

            icon, name = st.columns([1,6])
            avatar_url = get_initials_avatar(name=username, background="5de488")
            icon.image(avatar_url, width=45)
            with name:
                st.markdown(f"##### :green[{username}] <br> :grey[target user]", unsafe_allow_html=True)

            st.divider()

            sub_col1, sub_col2 = st.columns(2)

            with sub_col1:
                st.markdown(":grey[TOP GENRES]")
                for i, genre in enumerate(top_genres_1, start=1):
                    st.markdown(f":green[**{i}.**] {genre}")
            with sub_col2:
                st.markdown(":grey[TOP ARTISTS]")
                for i, artist in enumerate(top_artists_1, start=1):
                    st.markdown(f":green[**{i}.**] {artist}")

            st.markdown(":grey[LISTENER TYPE]")

            listener_types_1 = ""
            for type in types_1:
                listener_types_1 += f":green-badge[{type}] "

            st.markdown(listener_types_1)

        # SIMILAR USER
        with col2:

            icon, name = st.columns([1,6])
            avatar_url = get_initials_avatar(name=similar_user, background="b37eff")
            icon.image(avatar_url, width=45)
            with name:
                st.markdown(f"##### :violet[{similar_user}] <br> :grey[similar user]", unsafe_allow_html=True)

            st.divider()

            sub_col3, sub_col4 = st.columns(2)

            with sub_col3:
                st.markdown(":grey[TOP GENRES]")
                for i, genre in enumerate(top_genres_2, start=1):
                    st.markdown(f":violet[**{i}.**] {genre}")

            with sub_col4:
                st.markdown(":grey[TOP ARTISTS]")
                for i, artist in enumerate(top_artists_2, start=1):
                    st.markdown(f":violet[**{i}.**] {artist}")

            st.markdown(":grey[LISTENER TYPE]")

            listener_types_2 = ""
            for type in types_2:
                listener_types_2 += f":violet-badge[{type}] "

            st.markdown(listener_types_2)

        st.space("xxsmall")

        # SHARED
        st.markdown(f"**:grey[SHARED -- {username.upper()} AND {similar_user.upper()}]**")

        col1, col2, col3 = st.columns(3, border=True)

        with col1:
            st.markdown(":grey[GENRES]")
            if shared_genres:
                create_ombre_badge(list=shared_genres)
            else:
                st.markdown(f":grey[none]")
            st.space("xxsmall")

        with col2:
            st.markdown(":grey[ARTISTS]")
            if shared_artists:
                create_ombre_badge(list=shared_artists)
            else:
                st.markdown(f":grey[none]")
            st.space("xxsmall")

        with col3:
            st.markdown(":grey[LISTENER TYPES]")
            if shared_types:
                create_ombre_badge(list=shared_types)
            else:
                st.markdown(f":grey[none]")
            st.space("xxsmall")

        st.space("xxsmall")

        # HOUR SHARE COMPARISON (LINE CHART)
        with st.container(border=True):
            title, key = st.columns([2.6,1])
            with title:
                st.markdown("##### :green[:material/Schedule:] Hourly Share Comparison")
            with key:
                st.markdown(f"""
                <span style='display:inline-block; width:12px; height:12px; border-radius:50%;
                background-color:#5de488;'></span> {username} &nbsp;
                <span style='display:inline-block; width:12px; height:12px; border-radius:50%;
                background-color:#b37eff;'></span> {similar_user}""",
                unsafe_allow_html=True
            )
            # Get behavior metrics for both users
            user_1_metrics = get_user_behavior_metrics(user_id=user_id)
            user_2_metrics = get_user_behavior_metrics(user_id=similar_user_id)
            # Construct a 24-hour template dataframe (to fill missing hours for each user)
            full_day_df = pd.DataFrame({"hour": range(24)})
            # Construct hour-share dataframes for each user
            user_1_hour_share_df = pd.DataFrame(user_1_metrics["hour_shares"])
            user_2_hour_share_df = pd.DataFrame(user_2_metrics["hour_shares"])
            # Merge hour_share dataframe with 24-hour template for each user
            user_1_merged_df = pd.merge(full_day_df, user_1_hour_share_df, on="hour", how="left").fillna(0)
            user_2_merged_df = pd.merge(full_day_df, user_2_hour_share_df, on="hour", how="left").fillna(0)
            # Rename columns (in order to overlay line charts)
            user_1_merged_df.columns = ["Hour", username]
            user_2_merged_df.columns = ["Hour", similar_user]
            # Combine both user's dataframes into one
            merged_df = pd.merge(user_1_merged_df, user_2_merged_df, on="Hour", how="outer")
            merged_df = merged_df.set_index("Hour")

            # Display overlapping line chart in Streamlit
            st.line_chart(merged_df,
                          color=["#5de488","#b37eff"]
                          )
            st.caption("* Hour share represents the proportion of a user's total streams that fall within a given hour.")

        st.space("xxsmall")

        if not df.empty:

            # SHARED SONGS TABLE
            with st.container(border=True, height=350):
                st.markdown("##### :green[:material/Favorite:] Shared Songs")

                count_col, replay_col, comp_col = st.columns([3,1,1])
                count_col.markdown(f":grey[{len(df)} songs]")
                replay_col.markdown(":grey[avg replays]")
                comp_col.markdown(":grey[avg completion]")
                st.divider()

                for i, row in enumerate(df.itertuples(), start=1):
                    rank, icon, name, bar, val1, val2 = st.columns([0.1, 0.4, 1.2, 1.25, 1, 1])

                    with icon:
                        avatar_url = get_initials_avatar_2(name=row.Song)
                        st.image(avatar_url, width=45)
                    name.markdown(f"**{row.Song}** <br> :grey[{row.Artist}]", unsafe_allow_html=True)
                    # Avg replays b/t two users
                    val1.markdown(f":grey[:material/Repeat:] &nbsp; {row[4]:.1f}")
                    # Avg completion b/t two users
                    with val2:
                        progress, val = st.columns([2,1])
                        progress.progress(row[5])
                        val.markdown(f"{round(row[5]*100)}%")
                    st.divider()

            st.caption("* Avg Replays and Avg Completion are averaged across the two users.")

st.space("xxsmall")

# SIMILARITY SCORE BREAKDOWN
with st.expander(":green[Similarity Score Breakdown]"):

    st.space("xsmall")

    # Formula
    st.code("Similarity Score = 0.5 × Shared Songs + 0.3 × Replay Rate + 0.2 × Completion Rate", language=None)

    st.space("xsmall")

    st.write("Each user is scored using a weighted combination of three components. "
             "Shared Songs and Replay Rate are each normalized to a 0–1 scale relative "
             "to the highest value in the cohort.")

    st.space("xsmall")

    # Component cards
    components = [
        ("Shared Songs", "0.5", "The number of songs both users have streamed with sufficient "
         "engagement. The dominant signal — reflects how much overlap exists between two users' "
         "listening histories."),
        ("Replay Rate", "0.3", "How often the candidate user replayed the shared songs. Rewards "
         "deep engagement over passive streaming."),
        ("Completion Rate", "0.2", "The average share of each shared song the candidate user "
         "listened to. Rewards full listens over partial ones."),
    ]

    with st.container(border=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**{components[0][0]}**")
            st.caption(components[0][2])
        with col2:
            st.metric(label="Weight", value=f":green[{components[0][1]}]")

    with st.container(border=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**{components[1][0]}**")
            st.caption(components[1][2])
        with col2:
            st.metric(label="Weight", value=f":violet[{components[1][1]}]")

    with st.container(border=True):
        col1, col2 = st.columns([5, 1])
        with col1:
            st.markdown(f"**{components[2][0]}**")
            st.caption(components[2][2])
        with col2:
            st.metric(label="Weight", value=f":grey[{components[2][1]}]")

    st.space("xsmall")

    # Engagement filter
    st.markdown("#### Engagement Filter")
    st.write("Only streams with at least 2 replays and 50% completion are counted toward shared "
             "songs. This filters out incidental listens — a song only counts as shared when both "
             "users have demonstrated genuine interest.")

    st.caption("Weights were selected heuristically and could later be tuned experimentally "
               "or learned from user interaction data.")
