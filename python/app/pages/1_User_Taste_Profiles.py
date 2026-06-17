import streamlit as st
import pandas as pd
from datetime import datetime, time
from utils.user_taste_profiles import get_user_behavior_metrics, get_user_taste_profile
from utils.get_ids_and_maps import get_id_value_map, get_user_ids
from utils.queries import (get_liked_songs,
                           get_user_total_streams,
                           get_user_signup,
                           get_user_listening_hours
)

USERNAME_MAP = get_id_value_map(table="users", value_column="username")

# Convert peak_hour to 12-hour time
def convert_hour_datetime(hour_24: int) -> str:
        return time(hour_24).strftime("%I %p").lstrip("0")

# Generates avatar URL for similar users display -- code from Google AI
def get_initials_avatar(name, size=64, background="random"):
    return f"https://ui-avatars.com/api/?name={name}&size={size}&background={background}&rounded=true&bold=true"

# For initials w/ rounded square icons
def get_initials_avatar_2(name, size=64, background="random"):
    return f"https://ui-avatars.com/api/?name={name}&size={size}&background={background}&rounded=20&bold=true"

# Generates custom pill component w/ HTML & CSS -- code from Google AI
def custom_pill(label, bg_color, text_color, font_size=16, border_radius=10):
    pill_html = f"""
    &nbsp; :grey[LISTENER TYPE] <br>
    <span style="
        background-color: {bg_color};
        color: {text_color};
        padding: 8px 16px;
        font-size: {font_size}px;
        border-radius: {border_radius}px;
        font-weight: normal;
        display: inline-block;
        margin: 5px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    ">
        {label}
    </span>
    """
    st.markdown(pill_html, unsafe_allow_html=True)

# Adjusted for genre icons
def custom_pill_2(label, bg_color, text_color, font_size=25, border_radius=10):
    pill_html = f"""
    <span style="
        background-color: {bg_color};
        color: {text_color};
        padding: 0px 10px;
        font-size: {font_size}px;
        border-radius: {border_radius}px;
        font-weight: bold;
        display: inline-block;
        margin: 3px;
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
st.set_page_config(page_title="Music Analytics | Asa", page_icon="🎧", layout="wide")

# Sidebar for user selection
user_id = st.sidebar.selectbox(
    "Choose a user:",
     user_ids,
     index=4
)

# Get user's username
username = USERNAME_MAP[user_id]

# Get user taste profile
taste_profile = get_user_taste_profile(user_id)

# Get user behavior metrics
behavior_metrics = get_user_behavior_metrics(user_id)

# Get user's total streams
total_streams = get_user_total_streams(user_id=user_id)

# Get user's signup date
signup = get_user_signup(user_id=user_id)

# Convert signup date into "Month Year" format
date_object = datetime.strptime(signup[:7], "%Y-%m")
formatted_date = date_object.strftime("%b %Y")

# Separate listener types by commas
listener_types = "&ensp;·&ensp;".join(taste_profile["listener_types"])

st.header("User Taste Profile :green[:material/Account_Circle:] ")
col1, col2 = st.columns([3,1])
# Header & display selected user
with col1:
    st.space("xxsmall")
    profile, user = st.columns([1,12.5])
    with profile:
        avatar_url = get_initials_avatar(name=username)
        profile.image(avatar_url, width=45)
    user.markdown(f"##### :grey[User {user_id}] <br> :green[{username}]", unsafe_allow_html=True)
# Display listener type
with col2:
    custom_pill(f":material/Headphones:&ensp;{listener_types}", bg_color="#183828", text_color="#5de488")

st.space("xxsmall")

# Display key metrics
col1, col2, col3, col4 = st.columns(4, border=True)

col1.metric(label=":grey[**:green[:material/Stream:] STREAMS**]", value=total_streams)
col2.metric(label=":grey[**:green[:material/Favorite:] TOP GENRE**]", value=taste_profile["top_genres"][0]["genre"])
col3.metric(label=":grey[**:green[:material/Artist:] TOP ARTIST**]", value=taste_profile["top_artists"][0]["artist"])
col4.metric(label=":grey[**:green[:material/Calendar_Today:] ACTIVE SINCE**]", value=formatted_date)

# Construct a top genres dataframe
df1 = pd.DataFrame(taste_profile["top_genres"])
# Construct a top artists dataframe
df2 = pd.DataFrame(taste_profile["top_artists"])

col1, col2 = st.columns(2, border=True)

with col1:
    st.markdown("##### **:green[:material/Album:] Top genres**")

    # (Replaced with icons below)
    # for i, genre in enumerate(taste_profile["top_genres"], start=1):
    #     st.markdown(f"**:green[{i}]&ensp;{genre["genre"]}**")
    #     st.progress(genre["score"], text=f":grey[Affinity Score: {genre["score"]:.2f}]")

    # Display top genres with progress bars and total streams
    for i, row in enumerate(taste_profile["top_genres"], start=1):
        st.divider()
        colors = [
                  ("#183828", "#5de488"), # green
                  ("#172d43", "#3d9df4"), # blue
                  ("#2a2145", "#b37eff") # purple
                 ]
        rank, icon, name, bar, val = st.columns([0.3, 0.6, 1.2, 1.5, 0.5])
        rank.markdown(f":grey[**{i}**]")
        with icon:
            custom_pill_2(":material/Music_Note:", bg_color=colors[i-1][0], text_color=colors[i-1][1])
        name.markdown(f"**{row["genre"]}**")
        bar.progress(value=row["score"])
        val.markdown(f":grey[{row["score"]:.2f}]")
    st.divider()

with col2:
    st.markdown("##### **:green[:material/Artist:] Top artists**")
    # Initial display (replaced below with profile icons)
    # for i, artist in enumerate(taste_profile["top_artists"], start=1):
    #     st.markdown(f"**:green[{i}]&ensp;{artist["artist"]}**")
    #     st.progress(artist["score"], text=f":grey[Affinity Score: {artist["score"]:.2f}]")

    # Display top artists with progress bars and total streams
    for i, row in enumerate(taste_profile["top_artists"], start=1):
        st.divider()
        rank, icon, name, bar, val = st.columns([0.3, 0.5, 1.2, 1.5, 0.5])
        rank.markdown(f":grey[**{i}**]")
        with icon:
            avatar_url = get_initials_avatar(name=row["artist"])
            st.image(avatar_url, width=45)
        name.markdown(f"**{row["artist"]}**")
        bar.progress(value=row["score"])
        val.markdown(f":grey[{row["score"]:.2f}]")
    st.divider()

# Affinity Score Breakdown
with st.expander(":green[:material/info: Affinity Score Breakdown]"):

    # Display equation in colored box
    st.markdown("""
    <div style="background:#0a1f12;border-left:3px solid #5de488;border-radius:6px;padding:10px 14px;margin-bottom:1rem">
    <span style="font-family:monospace;font-size:14px;color:#b8f5ce">
        Affinity Score = 0.6 × Stream Share &nbsp;+&nbsp; 0.2 × Replay Rate &nbsp;+&nbsp; 0.2 × Completion Rate
    </span>
    <div style="font-size:14px;color:#6b7280;margin-top:6px">
        Stream Share and Replay Rate are normalized 0–1 relative to the user's highest-value genre.
    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(":grey[**COMPONENTS**]")

    col1, col2, col3 = st.columns(3, border=True)

    with col1:
        st.metric(label="Stream Share", value=":green[60%]")
        st.caption("""Total streams for this genre, normalized against the user's
                   most-streamed genre. The dominant signal.""")
    with col2:
        st.metric(label="Replay Rate", value=":green[20%]")
        st.caption("""Avg streams per distinct song in this genre. Rewards returning
                   to individual songs, not just volume.""")
    with col3:
        st.metric(label="Completion Rate", value=":green[20%]")
        st.caption("""Avg share of a song listened to across all streams in this genre.
                   Higher = user consistently listens through to the end. """)

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

    with st.container(key="grey_container"):

        col1, col2 = st.columns([0.15,5])

        col1.markdown("##### :grey[:material/Info:]")

        with col2:
            st.markdown(""":grey[
            The same formula applies to artists — Stream Share and Replay Rate are normalized
            against the user's most-streamed artist instead of genre.]
                        """, unsafe_allow_html=True)

# OLDER BREAKDOWNS (Simplified above)
#    # Genre Affinity Score
#     st.subheader(":green[Genre Affinity Score]")
#     st.write("""
#             Each genre is scored using a weighted combination of three components:\n

#             **Affinity Score**
#             `= 0.6 × Stream Share + 0.2 × Replay Rate + 0.2 × Completion Rate`\n

#             Stream Share and Replay Rate are each normalized to a 0–1 scale relative
#             to the highest value among all genres the user has streamed.\n

#             * :green[**Stream Share**] (weight: 0.60) — The user's total streams for a genre, normalized
#             against their most-streamed genre. This is the dominant signal, reflecting how much of the
#             user's overall listening time a genre captures.\n

#             * :green[**Replay Rate**] (weight: 0.20) — The average number of streams per distinct song
#             in a genre, normalized against the genre with the highest such average. This rewards genres
#             where the user returns to individual songs repeatedly, rather than just having many songs
#             streamed once.\n

#             * :green[**Completion Rate**] (weight: 0.20) — The average share of a song listened to across
#             all streams in a genre. A higher completion rate indicates the user consistently engages
#             with songs in the genre through to the end.\n

#             A genre scores highest when the user streams it heavily, replays its songs often,
#             and listens to them in full.
#             """)

#     # Artist Affinity Score
#     st.subheader(":green[Artist Affinity Score]")
#     st.write("""
#             Each artist is scored using the same weighted combination of three components:\n
#             **Affinity Score**
#             `= 0.6 × Stream Share + 0.2 × Replay Rate + 0.2 × Completion Rate`\n
#             Stream Share and Replay Rate are each normalized to a 0–1 scale relative
#             to the highest value among all artists the user has streamed.\n

#             * :green[**Stream Share**] (weight: 0.60) — The user's total streams for an artist, normalized
#             against their most-streamed artist. As the dominant signal, this reflects how central an
#             artist is to the user's overall listening activity.\n
#             * :green[**Replay Rate**] (weight: 0.20) — The average number of streams per distinct song by
#             the artist, normalized against the artist with the highest such average. A higher replay rate
#             indicates the user tends to revisit an artist's songs repeatedly, regardless of how many
#             distinct songs are involved..\n
#             * :green[**Completion Rate**] (weight: 0.20) — The average share of a song listened to across
#             all streams for the artist. Higher values indicate the user tends to listen to the artist's
#             songs all the way through rather than skipping away.\n

#             An artist scores highest when the user streams them frequently, revisits their individual
#             songs often, and listens to them fully.
#             """)

st.space("small")

# *** BEHAVIORAL METRICS ***

with st.container(border=True):
    # Behavioral Metrics Subheader
    st.markdown(f"##### **:green[:material/Leaderboard:] Behavioral Metrics**")

    # Create 4 side-by-side columns
    col1, col2, col3, col4 = st.columns(4)

    # Display diversity score
    diversity_score = round(behavior_metrics["diversity_score"], 3)
    col1.metric(label=":grey[:green[:material/Workspaces:] Diversity Score]", value=diversity_score)
    # Display avg completion rate
    avg_completion = behavior_metrics["avg_completion_rate"]
    col2.metric(label=":grey[:green[:material/Check:] Completion Rate]", value=f"{round(avg_completion*100)}%")
    # Display skip rate
    skip_rate = behavior_metrics["skip_rate"]
    col3.metric(label=":grey[:green[:material/Skip_Next:] Skip Rate]", value=f"{round(skip_rate*100)}%")
    # Display avg streams per song
    avg_streams_per_song = behavior_metrics["avg_streams_per_song"]
    col4.metric(label=":grey[:green[:material/Repeat:] Avg Replays]", value=f"{avg_streams_per_song}&times;")

# Diversity Score Breakdown -- custom css by Claude
with st.expander(":green[:material/info: Diversity Score Breakdown]"):
    st.markdown("""
    <div style="background:#0a1f12;border-left:3px solid #5de488;border-radius:6px;padding:10px 14px;margin-bottom:1rem">
    <span style="font-size:17px;color:#b8f5ce;font-family:Georgia,serif">
        Diversity Score = 1 &minus; &Sigma;(p<sub>i</sub><sup>2</sup>)
    </span>
    <div style="font-size:14px;color:#6b7280;margin-top:6px">
        where p<sub>i</sub> is each genre's share of the user's total streams. Squaring penalizes
        dominance — subtracting from 1 flips the scale so higher = more diverse.
    </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
<div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem;margin-top:.75rem">

<!-- User A -->
<div style="background:var(--background-color);border:0.5px solid #2a2a2a;border-radius:8px;padding:.75rem .875rem">
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
<div style="background:var(--background-color);border:0.5px solid #2a2a2a;border-radius:8px;padding:.75rem .875rem">
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

        # Original breakdown (replaced above)
        # # Diversity Score
        # st.subheader(":green[Diversity Score]")
        # st.markdown("""
        #         ##### Diversity Score $= 1 − \\sum (p_i^2)$

        #         where $p_i$ is the proportion of a user's total streams belonging to genre $i$.\n
        #         * Squaring each genre proportion penalizes dominance -- a genre that accounts for 80%
        #         of streams contributes 0.64 to the sum, while one that accounts for 20% contributes only 0.04.
        #         Subtracting from 1 flips the scale so that higher scores reflect greater diversity.\n
        #         * A user whose streams are spread evenly across many genres will have small proportions
        #         that sum to a low value, yielding a score close to 1. A user who streams almost exclusively
        #         one genre will have one proportion close to 1, pushing the score close to 0.
        #         """)
        # st.subheader(":green[Example:]")
        # st.write("""
        #         * :green[User A]: &emsp; 90% Rock, 10% Pop &emsp; &emsp; &emsp; &emsp; &emsp; &emsp; &emsp;
        #                         &emsp; &ensp; &emsp; → &emsp; Diversity ≈ low
        #         * :violet[User B]: &emsp; 25% Rock, 25% Pop, 25% Hip-Hop, 25% Jazz &emsp; → &emsp; Diversity ≈ high
        #         """)

# *** Listening hours chart ***

# Construct a 24-hour template dataframe
full_day_df = pd.DataFrame({"hour": range(24)})

# Construct an hour-share dataframe
hour_share_df = pd.DataFrame(behavior_metrics["hour_shares"])
# Merge hour_share data
merged_df = pd.merge(full_day_df, hour_share_df, on="hour", how="left").fillna(0)
# Relabel genre dataframe columns
merged_df.columns = ["Hour of Day", "Hour Share"]
# Change index
merged_df.set_index("Hour of Day")

st.space("small")

# Quick insights

# Get listening hours dataframe for a given user
hours_df = get_user_listening_hours()
user_df = hours_df.loc[hours_df["user_id"] == user_id]

# Get peak hour, peak window, "Day" or "Night" listener,
# best completion hour, workst skip hour

peak_hour, peak_hour_share = user_df.loc[user_df["total_streams"].idxmax(), ["hour", "hour_share"]]

best_comp_hour, comp_rate = tuple(user_df.loc[user_df["avg_completion_rate"].idxmax(), ["hour", "avg_completion_rate"]])

worst_skip_hour, skip_rate = tuple(user_df.loc[user_df["skip_rate"].idxmax(), ["hour", "skip_rate"]])

chart, insight = st.columns([2,1], border=True)


peak_hour = int(peak_hour)

# Classify listener type based on peak hour
if 6 <= peak_hour <= 11:
    hour_type = "Morning"
elif 12 <= peak_hour <= 17:
    hour_type = "Afternoon"
elif 18 <= peak_hour <= 22:
    hour_type = "Evening"
else:
    hour_type = "Late Night"

with chart:
    # Listening Hours Chart Subheader
    st.markdown("##### **:green[:material/Schedule:] Listening Hours**")
    # Display the Listening Hours bar chart
    st.bar_chart(merged_df, x="Hour of Day", y="Hour Share", color=["#5de488"])

with insight:
    st.markdown("##### :green[:material/Format_List_Bulleted:] Quick Insights")

    st.divider()

    # Replay rate
    col1, col2 = st.columns([0.5,5])
    with col1:
        st.markdown(":green-badge[:material/Window:]")
    with col2:
        st.markdown(f""" **Peak hour** <br>
                    :grey[Streams peak at
                    :green-badge[{convert_hour_datetime(int(peak_hour))}],
                    making up :green[{round(peak_hour_share*100)}%] of daily activity.] <br>
                    :green-badge[{hour_type}]
                    """, unsafe_allow_html=True)


    # Replay vs. skip
    col1, col2 = st.columns([0.5,5])
    with col1:
        st.markdown(":green-badge[:material/Check_Circle:]")
    with col2:
        st.markdown(f""" **Best completion hour** <br>
                    :grey[Most engagement at
                    :green-badge[{convert_hour_datetime(int(best_comp_hour))}],
                    with a completion rate of] :green[{round(comp_rate*100)}%]:grey[.]
                    """, unsafe_allow_html=True)
        st.progress(comp_rate)

    # Diversity vs. skip
    col1, col2 = st.columns([0.5,5])
    with col1:
        st.markdown(":green-badge[:material/Skip_Next:]")
    with col2:
        st.markdown(f""" **Worst skip hour** <br>
                    :grey[:green[{round(skip_rate*100)}%] of songs skipped at
                    :green-badge[{convert_hour_datetime(int(worst_skip_hour))}].]
                    """, unsafe_allow_html=True)
        st.progress(skip_rate)

st.space("small")

with st.container(border=True):
    # Liked Songs
    liked_songs = get_liked_songs(user_id)
    st.markdown("##### :green[:material/Favorite:] Liked Songs")
    st.markdown(f":grey[{len(liked_songs)} songs]")
    with st.container(border=True, height=400):
        for i, row in enumerate(liked_songs.itertuples(), start=1):
            rank, icon, name, bar, val = st.columns([0.1, 0.25, 1.2, 1.5, 0.5])

            with icon:
                avatar_url = get_initials_avatar_2(name=row.Song)
                st.image(avatar_url, width=45)
            name.markdown(f"**{row.Song}** <br> :grey[{row.Artist}]", unsafe_allow_html=True)
            val.markdown(f":red[:material/Favorite:] &nbsp; :grey[{row[3][:10]}]")
            st.divider()

with st.expander(":green[:material/Info: How are liked songs determined?]"):
    st.write(""":grey[
        Liked songs were generated probabilistically based on each user's streaming engagement.
        Songs were scored using a point system that rewards repeated streams and high completion
        rates — the higher the score, the greater the probability of being liked. The liked date
        reflects the user's most recent stream of that song.]
    """)

st.caption("See \"Synthetic Data Generation\" on the Database & ETL page for a full explanation.")

