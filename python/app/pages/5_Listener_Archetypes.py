import streamlit as st
import pandas as pd
import altair as alt
import numpy as np
from datetime import datetime
from utils.get_ids_and_maps import get_id_value_map, get_user_ids
from utils.user_taste_profiles import (get_user_behavior_metrics,
                                       classify_listener_type)
from utils.queries import (count_rows,
                           get_avg_hour_shares,
                           get_avg_diversity_score,
                           get_avg_distinct_songs,
                           get_avg_skip_rate,
                           get_avg_dom_genre_share,
                           get_avg_streams_per_song,
                           get_avg_completion_rate,
                           get_behavior_df)


DB_PATH = "/workspaces/273640407/music_db_project/db/music.db"

USER_IDS = get_user_ids()

# Function by Google AI for custom color badges
# (Streamlit does not currently support this feature natively)
def custom_pill(label, bg_color, text_color, font_size=25, border_radius=10):
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

# Functions by Claude AI for custom color progress bars
# (Streamlit does not currently support this feature natively)
def comparison_bar(label, value, overall, color, fmt=".0%"):
    pct = f"{value:{fmt}}"
    overall_pct = f"{overall:{fmt}}"
    bar_width = int(value * 100)
    overall_width = int(overall * 100)

    st.markdown(f"""
    <div style="margin-bottom: 8px;">
        <div style="display:flex; justify-content:space-between; font-size:14px; color:#e0f5e9; margin-bottom:3px">
            <span>{label}</span><span>{pct}</span>
        </div>
        <div style="background:#262730; border-radius:4px; height:8px; width:100%">
            <div style="background:{color}; width:{bar_width}%; height:8px; border-radius:4px"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:14px; color:gray; margin-top:3px">
            <span>overall avg</span><span>{overall_pct}</span>
        </div>
        <div style="background:#262730; border-radius:4px; height:8px; width:100%">
            <div style="background:gray; width:{overall_width}%; height:8px; border-radius:4px"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# For comparisons of values greater than 1
def comparison_bar_2(label, value, overall, color, fmt=".0%"):
    val_fmt = f"{value:{fmt}}"
    overall_fmt = f"{overall:{fmt}}"

    max_val = max(value, overall)
    val_width = int((value / max_val) * 100)
    overall_width = int((overall / max_val) * 100)

    st.markdown(f"""
    <div style="margin-bottom: 8px;">
        <div style="display:flex; justify-content:space-between; font-size:14px; color:#e0f5e9; margin-bottom:3px">
            <span>{label}</span><span>{val_fmt}</span>
        </div>
        <div style="background:#262730; border-radius:4px; height:8px; width:100%">
            <div style="background:{color}; width:{val_width}%; height:8px; border-radius:4px"></div>
        </div>
        <div style="display:flex; justify-content:space-between; font-size:14px; color:gray; margin-top:3px">
            <span>overall avg</span><span>{overall_fmt}</span>
        </div>
        <div style="background:#262730; border-radius:4px; height:8px; width:100%">
            <div style="background:gray; width:{overall_width}%; height:8px; border-radius:4px"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Shrink space before dividers
st.markdown(
    """
    <style>
        div[data-testid="stMarkdownContainer"] hr {
            margin-top: -20px;
            margin-bottom: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Store listener type dataframe to speed page
@st.cache_data
def build_listener_type_df(user_ids):
    rows = []
    for user_id in USER_IDS:
        metrics = get_user_behavior_metrics(user_id=user_id)
        listener_types = classify_listener_type(metrics)
        for listener_type in listener_types:
            rows.append({"user_id": user_id, "listener_type": listener_type})

    return pd.DataFrame(rows)

df = build_listener_type_df(USER_IDS)

archetype_counts = df["listener_type"].value_counts().reset_index()
archetype_counts.columns = ["Listener Type", "Count"]

archetype_descriptions = {
    "Focused Listener": "Repeatedly listens to a smaller set of music",
    "Explorer": "Samples broadly across genres and artists",
    "Completion-Oriented Listener": "Rarely skips and listens fully",
    "Casual Skipper": "Skips frequently",
    "Replay-Heavy Listener": "Returns to the same songs very often",
    "Night Listener": "Majority of listening happens late at night",
    "Day Listener": "Majority of listening happens during the day",
    "Genre Loyalist": "Listening is dominated by one genre",
    "Balanced Listener": "Moderate diversity with low skip tendency"
}

# Bg color first, text second
COLORS = {
            "green": ("#183828", "#5de488"),
            "blue": ("#172d43", "#3d9df4"),
            "violet": ("#2a2145", "#b37eff"),
            "red": ("#3f2429", "#ff6c6c"),
            "orange": ("#3e291a", "#ffbe46"),
            "yellow": ("#3d421e", "#ffffc3")
}

# Custom CSS to adjust metric label and value sizes -- from Google AI
st.markdown(
    """
    <style>
    /* Change the font size of the metric label */
    div[data-testid="stMetricLabel"] > div p {
        font-size: 20px !important;
    }

    /* Change the font size of the metric value (optional) */
    div[data-testid="stMetricValue"] > div {
        font-size: 30px !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Get counts for archetypes
COUNTS = {}
for archetype in archetype_descriptions:
    # Get row of given archetype
    filtered_df = archetype_counts[archetype_counts["Listener Type"] == archetype]

    if not filtered_df.empty:
        COUNTS[archetype] = filtered_df["Count"].iloc[0]
    else:
        COUNTS[archetype] = 0

# Get total users
TOTAL_USERS = count_rows("users")

# Get most common archetype (w/ count & share of users)
TOP_ARCHETYPE = archetype_counts.loc[archetype_counts["Count"].idxmax(), "Listener Type"]
TOP_COUNT = COUNTS[TOP_ARCHETYPE]
TOP_SHARE = TOP_COUNT / TOTAL_USERS

# Get least common archetype (w/ count & share of users)
RAREST_ARCHETYPE = archetype_counts.loc[archetype_counts["Count"].idxmin(), "Listener Type"]
RARE_COUNT = COUNTS[RAREST_ARCHETYPE]
RARE_SHARE = RARE_COUNT / TOTAL_USERS

# Get average number of archetypes per user
# (group by user_id, count rows for each user, then average)
AVG_ARCHETYPES = df.groupby("user_id").size().mean()

# Get overall user metrics (for comparison in profile cards)
OVERALL_DIVERSITY = get_avg_diversity_score(user_ids=USER_IDS)
OVERALL_DISTINCT_SONGS = get_avg_distinct_songs(user_ids=USER_IDS)
OVERALL_SKIP_RATE = get_avg_skip_rate(user_ids=USER_IDS)
OVERALL_DOM_GENRE_SHARE = get_avg_dom_genre_share(user_ids=USER_IDS)
OVERALL_REPLAYS = get_avg_streams_per_song(user_ids=USER_IDS)

# Sidebar for easier navigation
with st.sidebar:
    st.markdown("## :material/Headphones: Listener Archetypes")
    st.markdown("""
    :green-badge[[Archetype Distribution](#distribution)]
    :green-badge[[Profile Cards](#profiles)]
    :green-badge[[Archetype Overlap](#overlap)]
    :green-badge[[Metric Distributions](#distributions)]
    """)

# Set page title and layout
st.set_page_config(page_title="Music Analytics | Asa",
                   page_icon="🎧", layout="wide")

# HEADER
st.header(":green[:material/Sell:] Listener Archetypes")
st.space("xxsmall")
st.divider()

st.html('<a name="distribution"></a>')
# QUICK METRICS & DISTRIBUTION
st.markdown(":grey[**OVERVIEW**]")
graph, metrics = st.columns([2, 1.8], gap="medium")

with metrics:
    col1, col2 = st.columns(2, border=True)
    col1.metric(":grey[Total users]", TOTAL_USERS, help="Across all archetypes")
    col2.metric(":grey[Most common]", TOP_ARCHETYPE, delta=f"{round(TOP_SHARE * 100)}% of users",
                delta_color="off", delta_arrow="off")

    st.space("xxsmall")

    col3, col4 = st.columns(2, border=True)
    col3.metric(":grey[Avg archetypes / user]", round(AVG_ARCHETYPES, 1), help="Users often belong to multiple archetypes")
    col4.metric(":grey[Rarest archetype]", RAREST_ARCHETYPE, delta=f"{round(RARE_SHARE * 100)}% of users",
                delta_color="off", delta_arrow="off")

with graph:
    with st.container(border=True):
        st.markdown("##### :green[:material/Bar_Chart:] Archetype distribution")
        chart = alt.Chart(archetype_counts).mark_bar(color="#5de488", cornerRadiusEnd=3).encode(
            x=alt.X("Count", title=None, axis=alt.Axis(grid=False)),
            y=alt.Y("Listener Type", sort="-x", title=None),
            tooltip=["Listener Type", "Count"]
        ).properties(height=300)
        st.altair_chart(chart, use_container_width=True)


# PROFILE CARDS
st.html('<a name="profiles"></a>')
st.markdown("**:grey[PROFILE CARDS]**")

# DAY/NIGHT LISTENERS
col1, col2 = st.columns(2, border=True)

with col1:
    icon, name = st.columns([1,8])
    with icon:
        custom_pill(":material/Wb_Sunny:", bg_color=COLORS["orange"][0], text_color=COLORS["orange"][1])
    name.markdown("##### Day Listener")
    st.caption(archetype_descriptions["Day Listener"])

    # PEAK LISTENING HOURS (LINE CHART)

    # Get user ids of all Day Listeners
    day_listeners = df.loc[df["listener_type"] == "Day Listener", "user_id"].tolist()
    # Get dataframe with "Hour of Day" and "Avg Hour Share" columns for Day Listeners
    day_hour_shares = get_avg_hour_shares(user_ids=day_listeners)
    # Get avg peak hour for Day Listeners
    top_hour = day_hour_shares.loc[day_hour_shares["Avg Hour Share"].idxmax(), "Hour of Day"]
    # Convert to 12-hour format
    top_hour = datetime.strptime(top_hour, "%H").strftime("%I %p").lstrip("0")

    peak, count = st.columns(2, border=True)

    with peak:
        st.markdown(f":grey[avg peak hour] <br> **:orange[{top_hour}]**", unsafe_allow_html=True)

    with count:
        st.markdown(f":grey[users] <br> **:orange[{COUNTS["Day Listener"]}]**", unsafe_allow_html=True)

    # Display line chart
    st.caption("**Peak Listening Hours**")
    st.line_chart(day_hour_shares, x="Hour of Day", y="Avg Hour Share", color="#ffbe46")
    st.caption("Average proportion of total streams per hour, averaged across all Day Listeners.")


with col2:
    icon, name = st.columns([1,8])
    with icon:
        custom_pill(":material/Dark_Mode:", bg_color=COLORS["blue"][0], text_color=COLORS["blue"][1])
    name.markdown("##### Night Listener")
    st.caption(archetype_descriptions["Night Listener"])

    # PEAK LISTENING HOURS (LINE CHART)

    # Get user ids of all Night Listeners
    night_listeners = df.loc[df["listener_type"] == "Night Listener", "user_id"].tolist()
    # Get dataframe with "Hours" and "Avg Hour Share" columns for Night Listeners
    night_hour_shares = get_avg_hour_shares(user_ids=night_listeners)
    # Get avg peak hour for Night Listeners
    top_hour = night_hour_shares.loc[night_hour_shares["Avg Hour Share"].idxmax(), "Hour of Day"]
    # Convert to 12-hour format
    top_hour = datetime.strptime(top_hour, "%H").strftime("%I %p").lstrip("0")

    peak, count = st.columns(2, border=True)

    with peak:
        st.markdown(f":grey[avg peak hour] <br> **:blue[{top_hour}]**", unsafe_allow_html=True)

    with count:
        st.markdown(f":grey[users] <br> **:blue[{COUNTS["Night Listener"]}]**", unsafe_allow_html=True)

    # Display line chart
    st.caption("**Peak Listening Hours**")
    st.line_chart(night_hour_shares, x="Hour of Day", y="Avg Hour Share", color="#3d9df4")
    st.caption("Average proportion of total streams per hour, averaged across all Night Listeners.")

st.space("xxsmall")

# EXPLORER AND BALANCED LISTENERS
col1, col2 = st.columns(2, border=True)

with col1:
    icon, name = st.columns([1,8])
    with icon:
        custom_pill(":material/Explore:", bg_color=COLORS["red"][0], text_color=COLORS["red"][1])
    name.markdown("##### Explorer")
    st.caption(archetype_descriptions["Explorer"])

    # AVG DIVERSITY SCORE, AVG DISTINCT SONGS, USERS

    # Get user_ids of all Explorers
    explorers = df.loc[df["listener_type"] == "Explorer", "user_id"].tolist()

    # Get avg diversity score and avg distinct songs for Explorers
    avg_diversity_score = get_avg_diversity_score(user_ids=explorers)

    avg_distinct_songs = get_avg_distinct_songs(user_ids=explorers)

    col_a, col_b, col_c = st.columns(3, border=True)

    with col_a:
        st.markdown(f":grey[avg diversity score] <br> **:red[{avg_diversity_score}]**",
                    unsafe_allow_html=True)
    with col_b:
        st.markdown(f":grey[avg distinct songs] <br> **:red[{avg_distinct_songs}]**",
                    unsafe_allow_html=True)
    with col_c:
        st.markdown(f":grey[users] <br> **:red[{COUNTS["Explorer"]}]**",
                    unsafe_allow_html=True)

    with st.container(border=False):
        comparison_bar("diversity score", avg_diversity_score, OVERALL_DIVERSITY, color="#ff6c6c", fmt=".2f")
        st.space("xxsmall")

with col2:
    icon, name = st.columns([1,8])
    with icon:
        custom_pill(":material/Tune:", bg_color=COLORS["violet"][0], text_color=COLORS["violet"][1])
    name.markdown("##### Balanced Listener")
    st.caption(archetype_descriptions["Balanced Listener"])

    # AVG DIVERSITY SCORE, AVG SKIP RATE

    # Get user_ids of all Balanced Listeners
    balanced_listeners = df.loc[df["listener_type"] == "Balanced Listener", "user_id"].tolist()

    # Get avg diversity score and avg skip rate for Balanced Listeners
    avg_diversity_score = get_avg_diversity_score(user_ids=balanced_listeners)

    avg_skip_rate = get_avg_skip_rate(user_ids=balanced_listeners)

    col_a, col_b, col_c = st.columns(3, border=True)

    with col_a:
        st.markdown(f":grey[avg diversity score] <br> **:violet[{avg_diversity_score}]**",
                    unsafe_allow_html=True)
    with col_b:
        st.markdown(f":grey[avg skip rate] <br> **:violet[{round(avg_skip_rate*100)}%]**",
                    unsafe_allow_html=True)
    with col_c:
        st.markdown(f":grey[users] <br> **:violet[{COUNTS["Balanced Listener"]}]**",
                    unsafe_allow_html=True)

    with st.container(border=False):
        comparison_bar("skip rate", avg_skip_rate, OVERALL_SKIP_RATE, color="#b37eff", fmt=".2f")
        st.space("xxsmall")

st.space("xxsmall")

# GENRE LOYALIST AND CASUAL SKIPPER
col1, col2 = st.columns(2, border=True)

with col1:
    icon, name = st.columns([1,8])
    with icon:
        custom_pill(":material/Music_Note_2:", bg_color=COLORS["green"][0], text_color=COLORS["green"][1])
    name.markdown("##### Genre Loyalist")
    st.caption(archetype_descriptions["Genre Loyalist"])

    # AVG DOMINANT GENRE SHRARE

    # Get user_ids of all Genre Loyalists
    genre_loyalists = df.loc[df["listener_type"] == "Genre Loyalist", "user_id"].tolist()

    avg_dom_genre_share = get_avg_dom_genre_share(user_ids=genre_loyalists)

    col_a, col_b = st.columns(2, border=True)

    with col_a:
        st.markdown(f":grey[avg dominant genre share] <br> **:green[{avg_dom_genre_share}]**",
                    unsafe_allow_html=True)
    with col_b:
        st.markdown(f":grey[users] <br> **:green[{COUNTS["Genre Loyalist"]}]**",
                    unsafe_allow_html=True)

    with st.container(border=False):
        comparison_bar("dom. genre", avg_dom_genre_share, OVERALL_DOM_GENRE_SHARE, color="#5de488", fmt=".2f")
        st.space("xxsmall")

with col2:
    icon, name = st.columns([1,8])
    with icon:
        custom_pill(":material/Skip_Next:", bg_color=COLORS["yellow"][0], text_color=COLORS["yellow"][1])
    name.markdown("##### Casual Skipper")
    st.caption(archetype_descriptions["Casual Skipper"])

    # AVG SKIP RATE

    # Get user_ids of all Casual Skippers
    casual_skippers = df.loc[df["listener_type"] == "Casual Skipper", "user_id"].tolist()

    # Get avg skip rate for Casual Skippers
    avg_skip_rate = get_avg_skip_rate(user_ids=casual_skippers)

    # Get avg completion rate for Casual Skippers
    avg_completion_rate = get_avg_completion_rate(user_ids=casual_skippers)

    col_a, col_b, col_c = st.columns(3, border=True)

    with col_a:
        st.markdown(f":grey[avg skip rate] <br> **:yellow[{round(avg_skip_rate*100)}%]**",
                    unsafe_allow_html=True)
    with col_b:
        st.markdown(f":grey[avg completion] <br> **:yellow[{round(avg_completion_rate*100)}%]**",
                    unsafe_allow_html=True)
    with col_c:
        st.markdown(f":grey[users] <br> **:yellow[{COUNTS["Casual Skipper"]}]**",
                    unsafe_allow_html=True)

    with st.container(border=False):
        comparison_bar("skip rate", avg_skip_rate, OVERALL_SKIP_RATE, color="#ffffc3", fmt=".2f")
        st.space("xxsmall")

st.space("xxsmall")

# FOCUSED AND REPLAY-HEAVY LISTENERS
col1, col2 = st.columns(2, border=True)

with col1:
    icon, name = st.columns([1,8])
    with icon:
        custom_pill(":material/Repeat:", bg_color=COLORS["orange"][0], text_color=COLORS["orange"][1])
    name.markdown("##### Focused Listener")
    st.caption(archetype_descriptions["Focused Listener"])

    # AVG DIVERSITY SCORE, AVG STREAMS PER SONG

    # Get user_ids of all Focused Listeners
    focused = df.loc[df["listener_type"] == "Focused Listener", "user_id"].tolist()

    # Get avg diversity score and avg streams per song for Focused Listeners
    avg_diversity_score = get_avg_diversity_score(user_ids=focused)

    avg_streams_per_song = get_avg_streams_per_song(user_ids=focused)

    col_a, col_b, col_c = st.columns(3, border=True)

    with col_a:
        st.markdown(f":grey[avg diversity score] <br> **:orange[{avg_diversity_score}]**",
                    unsafe_allow_html=True)
    with col_b:
        st.markdown(f":grey[avg streams/song] <br> **:orange[{avg_streams_per_song}]**",
                    unsafe_allow_html=True)
    with col_c:
        st.markdown(f":grey[users] <br> **:orange[{COUNTS["Focused Listener"]}]**",
                    unsafe_allow_html=True)

    with st.container(border=False):
        comparison_bar("diversity score", avg_diversity_score, OVERALL_DIVERSITY, color="#ffbe46", fmt=".2f")
        st.space("xxsmall")

with col2:
    icon, name = st.columns([1,8])
    with icon:
        custom_pill(":material/Replay:", bg_color=COLORS["blue"][0], text_color=COLORS["blue"][1])
    name.markdown("##### Replay-Heavy")
    st.caption(archetype_descriptions["Replay-Heavy Listener"])

    # AVG STREAMS PER SONG

    # Get user_ids of all Replay-Heavy Listeners
    replay_heavy = df.loc[df["listener_type"] == "Replay-Heavy Listener", "user_id"].tolist()

    # Get avg streams per song for Replay-Heavy Listeners

    avg_streams_per_song = get_avg_streams_per_song(user_ids=replay_heavy)

    col_a, col_b = st.columns(2, border=True)

    with col_a:
        st.markdown(f":grey[avg streams/song] <br> **:blue[{avg_streams_per_song}]**",
                    unsafe_allow_html=True)
    with col_b:
        st.markdown(f":grey[users] <br> **:blue[{COUNTS["Replay-Heavy Listener"]}]**",
                    unsafe_allow_html=True)

    with st.container(border=False):
        comparison_bar_2("streams / song", avg_streams_per_song, OVERALL_REPLAYS, color="#3d9df4", fmt=".2f")
        st.space("xxsmall")

st.space("xxsmall")

# COMPLETION-ORIENTED LISTENER
with st.container(border=True):
    icon, name = st.columns([1,17])
    with icon:
        custom_pill(":material/Check:", bg_color=COLORS["violet"][0], text_color=COLORS["violet"][1])
    name.markdown("##### Completion-Oriented")
    st.caption(archetype_descriptions["Completion-Oriented Listener"])

    # AVG COMPLETION RATE, AVG SKIP RATE

    # Get user_ids of all Completion-Oriented Listeners
    completion_oriented = df.loc[df["listener_type"] == "Completion-Oriented Listener", "user_id"].tolist()

    # Get avg completion and skip rates for Completion-Oriented Listeners
    avg_completion_rate = get_avg_completion_rate(user_ids=completion_oriented)

    avg_skip_rate = get_avg_skip_rate(user_ids=completion_oriented)

    if avg_completion_rate is not None and avg_skip_rate is not None:
        col_a, col_b, col_c = st.columns(3, border=True)

        with col_a:
            st.markdown(f":grey[avg completion] <br> **:violet[{round(avg_completion_rate*100)}%]**",
                        unsafe_allow_html=True)
        with col_b:
            st.markdown(f":grey[avg skip rate] <br> **:violet[{round(avg_skip_rate*100)}%]**",
                        unsafe_allow_html=True)
        with col_c:
            st.markdown(f":grey[users] <br> **:violet[{COUNTS["Completion-Oriented Listener"]}]**",
                        unsafe_allow_html=True)

    else:
        st.write(":grey[No users currently match this archetype.]")

st.space("xxsmall")

# ARCHETYPE OVERLAP HEATMAP
st.html('<a name="overlap"></a>')

# Pivot df to wide format -- one row per user, one column per archetype
wide_df = df.copy()
wide_df["value"] = 1
wide_df = wide_df.pivot_table(index="user_id",
                              columns="listener_type",
                              values="value",
                              fill_value=0)

# Compute co-occurence matrix
cooccurrence = wide_df.T.dot(wide_df)

# Remove the upper tiangle:

# Create a matrix the same size as the co-occurrence matrix
# filled entirely with 1s
matrix = np.ones(cooccurrence.shape)

# Keep elements in the lower triangle,
# change all elements above the diagonal to 0, and
# convert the 1s into True and 0s into False
mask = np.tril(matrix, k=0).astype(bool)
cooccurrence_masked = cooccurrence.where(mask)

# Convert to long format for altair
cooccurrence_long = cooccurrence_masked.reset_index().melt(id_vars="listener_type",
                                                           var_name="listener_type_2",
                                                           value_name="count")

# Drop None values from "count" column (i.e. drop nulled upper triangle)
cooccurrence_long = cooccurrence_long.dropna(subset=["count"])

chart = alt.Chart(cooccurrence_long).mark_rect().encode(
    x=alt.X("listener_type_2:O", title="Listener Type 2"),
    y=alt.Y("listener_type:O", title="Listener Type"),
    color=alt.Color("count:Q", title="users in both", scale=alt.Scale(scheme="greens")),
    tooltip=["listener_type", "listener_type_2", "count"]
)

with st.container(border=True):
    st.markdown("##### :green[:material/Join:] Archetype Overlap")
    st.caption("Each cell shows the number of users who belong to both archetypes. " \
            "Diagonal cells show the total count of each archetype.")
    st.space("small")
    st.altair_chart(chart)


st.space("xxsmall")

# METRIC DISTRIBUTIONS BY ARCHETYPE
st.html('<a name="distributions"></a>')

# Get behavior df with the following columns:
# "user_id", "skip_rate", "avg_streams_per_song", "avg_completion_rate",
# "diversity_score", "dominant_genre_share"
behavior_df = get_behavior_df()

# Join listener types df with behavior metrics df
merged_df = df.merge(behavior_df, on="user_id")

# BOX PLOTS
with st.container(border=True):
    st.markdown("##### :green[:material/Bar_Chart:] Metric Distributions by Archetype")
    metric = st.pills("Metric", [
        "Skip Rate",
        "Avg Streams Per Song",
        "Diversity Score",
        "Dominant Genre Share",
        "Avg Completion Rate"
    ], default="Skip Rate")

    st.space("xxsmall")

    st.markdown(f":grey[**{metric} by Listener Type**]")

    chart = alt.Chart(merged_df).mark_boxplot(color="#5de488").encode(
                x=alt.X("listener_type:O", title="Listener Type"),
                y=alt.Y(f"{metric}:Q", title=metric),
                tooltip=["listener_type", f"{metric}"]
    )
    st.altair_chart(chart)


