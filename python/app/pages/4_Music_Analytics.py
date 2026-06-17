import streamlit as st
import pandas as pd
import altair as alt
import plotly.express as px
import plotly.graph_objects as go
from datetime import time
from scipy.stats import pearsonr
from utils.user_taste_profiles import get_user_behavior_metrics, get_user_taste_profile
from utils.queries import (
    count_rows,
    get_total_listening_hours,
    get_country_counts,
    get_top_genres,
    get_top_songs,
    get_top_artists,
    get_top_replayed_songs,
    get_genre_shares,
    get_hour_analytics,
    get_behavior_data,
    get_diversity_scores,
    get_user_behavior_metrics,
    get_user_diversity_metrics,
    get_users,
    get_streams_by_month
)

DB_PATH = "/workspaces/music-streaming-project/db/music.db"

MINT_PALETTE = [
    "#143d26", "#1b5c38", "#27854e", "#38ad69", "#5de488",
    "#80e8a2", "#a2f0b8", "#c3f5d1", "#dffadc", "#effcee"
]


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

# CSS for grey container 5
css = """
    <style>
    .st-key-grey_container_5 {
        background-color: #262730;
        padding: 20px;
        border-radius: 10px;
    }
    </style>
    """
st.html(css)

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

# Generates custom pill component w/ HTML & CSS -- code from Google AI
def custom_pill(label, bg_color, text_color, font_size=35, border_radius=10):
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

# Set page title and layout
st.set_page_config(page_title="Music Analytics | Asa",
                   page_icon="🎧", layout="wide")

# Header
st.header(":green[:material/Bar_Chart:] Music Analytics")
st.space("xxsmall")
st.divider()

# Sidebar w/ quick links
with st.sidebar:
    st.markdown("## :material/Bar_Chart: Music Analytics")
    st.markdown("""
    :green-badge[[Platform Overview](#overview)] <br>
    :green-badge[[Top Content](#top-content)] <br>
    :green-badge[[Genre Distribution](#genres)] <br>
    :green-badge[[Streams by Month](#streams)] <br>
    :green-badge[[Listening Time](#listening-time)] <br>
    :green-badge[[User Behavior](#user-behavior)]
    """, unsafe_allow_html=True)


# ** PLATFORM OVERVIEW METRICS **

# Get total users
TOTAL_USERS = count_rows("users")
# Get total streams
TOTAL_STREAMS = count_rows("streams")
# Get total artists
TOTAL_ARTISTS = count_rows("artists")
# Get total songs
TOTAL_SONGS = count_rows("songs")
# Get total genres
TOTAL_GENRES = count_rows("genres")
# Get total listening hours
TOTAL_HOURS = get_total_listening_hours()
# Get countries and their user counts
country_counts_df = get_country_counts()

# Generates avatar URL for similar users display -- code from Google AI
def get_initials_avatar(name, size=64, background="random"):
    return f"https://ui-avatars.com/api/?name={name}&size={size}&background={background}&rounded=10&bold=true"

# With circle icons
def get_initials_avatar_circle(name, size=64, background="random"):
    return f"https://ui-avatars.com/api/?name={name}&size={size}&background={background}&rounded=true&bold=true"

st.html('<a name="overview"></a>')
st.markdown("##### :green[:material/Dashboard:] Platform Overview")

col1, col2, col3 = st.columns([2,1,1])

with col1:
    with st.container(border=True, height=165):
        # df with "year_month" and "total_streams" columns
        monthly_streams_df = get_streams_by_month()
        this_year_streams = monthly_streams_df[monthly_streams_df["year_month"] >= "2025-06"]["total_streams"].sum()
        last_year_streams = monthly_streams_df[(monthly_streams_df["year_month"] >= "2024-06") &
                                            (monthly_streams_df["year_month"] < "2025-06")]["total_streams"].sum()
        yoy_change = (this_year_streams - last_year_streams) / last_year_streams
        stream, delta = st.columns([3,2])
        stream.metric(label=":grey[**:green[:material/Stream:] STREAMS**]", value=f"{TOTAL_STREAMS:,}")
        with delta:
            st.markdown(f":green-badge[:material/Arrow_Upward: {yoy_change*100:.1f}% vs. previous year]")

        with st.container():
            col_a, col_b = st.columns([0.3,5])
            col_a.markdown("##### :grey[:material/Info:]")
            col_b.caption("YoY delta reflects recency bias in stream generation, not organic platform growth.")

with col2:
    with st.container(border=True, height=165):
        st.space("xxsmall")
        icon, val = st.columns([1.3,3])
        with icon:
            custom_pill(":material/Group:", bg_color="#183828", text_color="#5de488")
        val.metric(label=":grey[**USERS**]", value=f"{TOTAL_USERS}")

with col3:
    with st.container(border=True, height=165):
        st.space("xxsmall")
        users_df = get_users()
        premium_users = (users_df["subscription_type"] == "premium").sum()
        proportion = premium_users / TOTAL_USERS
        # st.metric(label="Premium User Share", value=f":green[{proportion*100:.1f}%]")
        icon, val = st.columns([1.3,3])
        with icon:
            custom_pill(":material/Schedule:", bg_color="#183828", text_color="#5de488")
        val.metric(label=":grey[**HOURS**]", value=f"{round(TOTAL_HOURS/1000,1)}k")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True, height=105):
        icon, val = st.columns([1,3])
        with icon:
            custom_pill(":material/Artist:", bg_color="#183828", text_color="#5de488")
        val.metric(label=":grey[**ARTISTS**]", value=f"{round(TOTAL_ARTISTS/1000,1)}k")

with col2:
    with st.container(border=True, height=105):
        icon, val = st.columns([1,3])
        with icon:
            custom_pill(":material/Library_Music:", bg_color="#183828", text_color="#5de488")
        val.metric(label=":grey[**SONGS**]", value=f"{round(TOTAL_SONGS/1000,1)}k")

with col3:
    with st.container(border=True,height=105):
        icon, val = st.columns([1,3])
        with icon:
            custom_pill(":material/Sell:", bg_color="#183828", text_color="#5de488")
        val.metric(label=":grey[**GENRES**]", value=f"{TOTAL_GENRES}")

st.space("xxsmall")


# *** TOP CONTENT ***
st.html('<a name="top-content"></a>')
col1, col2 = st.columns(2)

with col1:

    with st.container(border=True, height=460):

        # * TOP SONGS *
        st.markdown("##### :green[:material/Music_Note_2:] Top Songs")

        metric = st.pills("Rank by:",
                            [
                                "Total Streams",
                                "Avg Replays"
                            ],
                            label_visibility="collapsed",
                            default="Total Streams"
                            )

        if metric == "Total Streams":

            # TOP 10 STREAMED SONGS
            col_a, col_b = st.columns([6.5, 1])
            col_a.markdown("**:grey[Top 10 Streamed Songs]**")
            col_b.caption("streams")

            top_songs_df = get_top_songs(limit=10)

            # Create an Altair bar chart to order top streamed songs by descending streams (removed)
            chart = alt.Chart(top_songs_df).mark_bar(color="#5de488").encode(
                        x="Total Streams",
                        y=alt.Y("Song", sort="-x"),
                        tooltip=["Song", "Artist", "Total Streams"]
                        )

            with st.container(height=300, border=False):

                MAX_STREAMS = top_songs_df["Total Streams"].max()
                # Display top songs with progress bars and total streams
                for i, row in enumerate(top_songs_df.itertuples(), start=1):
                    rank, icon, name, bar, val = st.columns([0.3, 0.5, 1.2, 1.5, 0.5])
                    rank.markdown(f":grey[**{i}**]")
                    with icon:
                        avatar_url = get_initials_avatar(name=row.Song)
                        st.image(avatar_url, width=45)
                    name.markdown(f"**{row.Song}** <br> :grey[{row.Artist}]", unsafe_allow_html=True)
                    bar.progress(value=row[3]/MAX_STREAMS)
                    val.markdown(f":grey[{row[3]:,}]")

        else:

            # TOP 10 REPLAYED SONGS
            col_a, col_b = st.columns([5, 1])
            col_a.markdown("**:grey[Top 10 Replayed Songs]**")
            col_b.caption("avg replays")

            top_replayed_songs_df = get_top_replayed_songs(limit=10)

            # Create an Altair bar chart to order top replayed songs by descending replays (Removed)
            chart = alt.Chart(top_replayed_songs_df).mark_bar(color="#5de488").encode(
                        x="Avg Replays",
                        y=alt.Y("Song", sort="-x"),
                        tooltip=["Song", "Artist", "Avg Replays"]
                        )


            with st.container(height=300, border=False):

                MAX_STREAMS = top_replayed_songs_df["Avg Replays"].max()
                # Display top songs with progress bars and total streams
                for i, row in enumerate(top_replayed_songs_df.itertuples(), start=1):
                    rank, icon, name, bar, val = st.columns([0.3, 0.5, 1.2, 1.5, 0.5])
                    rank.markdown(f":grey[**{i}**]")
                    with icon:
                        avatar_url = get_initials_avatar(name=row.Song)
                        st.image(avatar_url, width=45)
                    name.markdown(f"**{row.Song}** <br> :grey[{row.Artist}]", unsafe_allow_html=True)
                    bar.progress(value=row[3]/MAX_STREAMS)
                    val.markdown(f":grey[{row[3]:,}]")
                # Clarification:
                st.caption("Ranked by average replays per listener rather than total replays, " \
                        "to surface songs that users genuinely return to repeatedly regardless " \
                        "of overall popularity.")

with col2:

    with st.container(border=True, height=460):

        # * TOP ARTISTS *
        st.markdown("##### :green[:material/Artist:] Top Artists")

        top_artists_df = get_top_artists(limit=10)

        top_3 = tuple(top_artists_df["Artist"].iloc[0:3])

        artist_str = ""
        for artist in top_3:
            artist_str += f":green-badge[{artist}] "

        # Display top 3 artists
        st.markdown(artist_str)

        col_a, col_b = st.columns([6.5, 1])
        col_a.markdown("**:grey[Top 10 Streamed Artists]**")
        col_b.caption("streams")

        # Create an Altair bar chart to order top artists by descending streams
        chart = alt.Chart(top_artists_df).mark_bar(color="#5de488").encode(
                    x="Total Streams",
                    y=alt.Y("Artist", sort="-x"),
                    tooltip=["Artist", "Total Streams"]
                    )

        with st.container(height=300, border=False):

            MAX_STREAMS = top_artists_df["Total Streams"].max()
            # Display top songs with progress bars and total streams
            for i, row in enumerate(top_artists_df.itertuples(), start=1):
                rank, icon, name, bar, val = st.columns([0.3, 0.5, 1.2, 1.5, 0.5])
                rank.markdown(f":grey[**{i}**]")
                with icon:
                    avatar_url = get_initials_avatar_circle(name=row.Artist)
                    st.image(avatar_url, width=45)
                name.markdown(f"**{row.Artist}**")
                bar.progress(value=row[2]/MAX_STREAMS)
                val.markdown(f":grey[{row[2]:,}]")


st.space("small")

st.html('<a name="genres"></a>')

with st.container(border=True):

    # TOP GENRES
    col1, col2 = st.columns([4,1])

    col1.markdown("##### :green[:material/Genres:] Top Genres")

    with col2:
        mode = st.pills("", ["Top 5", "Distribution"], label_visibility="collapsed", default="Top 5")

    # Get top 10 genres (by total streams)
    top_genres_df = get_top_genres(limit=10)

    # Normalize to the max in the top 10 (for genre progress bars)
    max_streams = top_genres_df["Total_Streams"].max()
    top_genres_df["Progress"] = top_genres_df["Total_Streams"] / max_streams

    # Get top 3 genres for displaying
    top_3 = tuple(top_genres_df["Genre"].iloc[0:3])

    # Display top 3 genres (removed)
    genre_str = ""
    for genre in top_3:
        genre_str += f":green-badge[{genre}] "

    # Create an Altair bar chart to order top genres by descending streams
    chart = alt.Chart(top_genres_df).mark_bar(color="#5de488").encode(
                x="Total_Streams",
                y=alt.Y("Genre", sort="-x"),
                tooltip=["Genre", "Total_Streams"]
                )

    # Get genre shares df with columns "Genre" and "Genre Share"
    genre_shares_df = get_genre_shares()

    # Sort values descending and get top 10 genre
    genre_shares_df_sorted = genre_shares_df.sort_values(by="Genre Share", ascending=False)
    top_10_genres_df = genre_shares_df_sorted.head(10)

    # Sum the remaining rows
    others_sum  = genre_shares_df_sorted.iloc[10:]["Genre Share"].sum()

    # Create an "other" row
    others_df = pd.DataFrame({
        "Genre": ["other"],
        "Genre Share": [others_sum]
    })

    # Combine top 10 with the "other" row
    final_df = pd.concat([top_10_genres_df, others_df], ignore_index=True)

    top_genre_share = top_10_genres_df.iloc[0]["Genre Share"]

    # Top genres & stat cards
    col1, col2 = st.columns([2,1])
    with col1:
        # Create columns for displaying ranks, progress bars, and streams side-by-side
        col_a, col_b = st.columns([9,1])
        col_a.markdown(genre_str)
        col_b.caption("streams")

        with st.container(height=200, border=False):
            # Display top genres with progress bars and total streams
            for i, row in enumerate(top_genres_df.itertuples(), start=1):
                rank_col, name_col, bar_col, space_col, val_col = st.columns([0.25, 1.5, 3, 0.1, 0.5])
                rank_col.markdown(f":grey[**{i}**]")
                name_col.markdown(row.Genre)
                bar_col.progress(value=row.Progress)
                val_col.markdown(f"{row.Total_Streams:,}")

    with col2:
        with st.container(border=True):
            st.markdown(f":grey[Top genre share] <br> :green[**{round(top_genre_share*100,1)}%**]", unsafe_allow_html=True)
            st.caption("of all streams")
        with st.container(border=True):
            st.markdown(f":grey[Total genres] <br> :green[**{TOTAL_GENRES}**]", unsafe_allow_html=True)
            st.caption("across the platform")

    if mode == "Top 5":
        pass

    if mode == "Distribution":

        st.space("medium")

        pie_colors = [
            '#39e06c',  # Segment 1
            '#46e275',  # Segment 2
            '#53e37e',  # Segment 3
            '#5de488',  # Base Color
            '#6de691',  # Segment 5
            '#7de99a',  # Segment 6
            '#8deda4',  # Segment 7
            '#9df0ad',  # Segment 8
            '#adf3b7',  # Segment 9
            '#bdf6c1',  # Segment 10
            '#ccf9ca'   # Segment 11
        ]

        reverse_colors = pie_colors[::-1]

        # Generate plotly pie chart (first one removed)
        fig = px.pie(final_df, names="Genre", values="Genre Share", title=None,
                    color_discrete_sequence=pie_colors, hole=0.4)

        fig = go.Figure(data=[go.Pie(
            labels=final_df["Genre"],
            values=final_df["Genre Share"],
            hole=0.4, # Controls the size of the hole (0 to 1)
            textinfo="label",
            hoverinfo="label+value",
            marker_colors=reverse_colors
        )])

        top_genre_share = top_10_genres_df.iloc[0]["Genre Share"]
        # Add text in the middle
        fig.update_layout(
            annotations=[{
                "text": f"top genre<br>{round(top_genre_share*100,1)}%", # Use <br> for multi-line text
                "showarrow": False,
                "font": {"size": 20, "color": "#9c9d9f", "family": "Source Sans"},
                "x": 0.5, # Center X
                "y": 0.5  # Center Y
            }],
            showlegend=True,
            margin=dict(t=0, b=0, l=0, r=0)
        )

        # Display pie chart in Streamlit
        st.plotly_chart(fig)
        st.caption("Note: genres outside the top 10 are grouped into \"other\"")


st.space("xxsmall")


st.html('<a name="streams"></a>')
with st.container(border=True):

    st.markdown("##### :green[:material/Calendar_Clock:] Streams by Month")

    st.space("xxsmall")

    st.bar_chart(monthly_streams_df.set_index("year_month"), color="#5de488")

    with st.container(key="grey_container_5"):

        col1, col2 = st.columns([0.15,5])

        col1.markdown("##### :grey[:material/Info:]")

        with col2:
            st.markdown(""" **Recency bias** <br>
            :grey[Stream timestamps were generated with a recency bias relative to the database seed date.
            Sparse activity before mid-2025 reflects this intentional distribution, not actual platform growth. <br>
            :grey-badge[:green[40%] last month] :grey-badge[:green[40%] last year]  :grey-badge[:green[20%] older]           ]
                        """, unsafe_allow_html=True)


st.space("xxsmall")

st.html('<a name="listening-time"></a>')

col1, col2 = st.columns([2,1], border=True)
with col1:

    # ** LISTENING TIME ANALYTICS **

    st.markdown("##### :green[:material/Schedule:] Listening Time Analytics")

    metric = st.pills("Metric",
                        [
                            "Total Streams",
                            "Hour Share",
                            "Completion Rate",
                            "Skip Rate"
                        ],
                        default="Total Streams"
                        )

    st.space("xsmall")

    # Get dataframe with the following columns:
    # "Hour of Day", "Total Streams", "Avg Hour Share", "Avg Completion Rate", "Avg Skip Rate"
    df = get_hour_analytics()

    total_streams = df[["Hour of Day", "Total Streams"]]
    hour_share = df[["Hour of Day", "Avg Hour Share"]]
    comp_rate = df[["Hour of Day", "Avg Completion Rate"]]
    skip_rate = df[["Hour of Day", "Avg Skip Rate"]]

    # Make line charts for each metric
    if metric == "Total Streams":
        st.markdown("**:grey[Total Streams by Hour]**")
        st.line_chart(total_streams, x="Hour of Day", y="Total Streams", color="#5de488")

    elif metric == "Hour Share":
        st.markdown("**:grey[Average User Activity by Hour]**")

        st.line_chart(hour_share, x="Hour of Day", y="Avg Hour Share", color="#5de488")

        st.caption("A user's hour share is the proportion of their total streams that " \
                "fall within a given hour. The average hour share is then taken across all users " \
                "to show how listening activity is distributed throughout the day.")

    elif metric == "Completion Rate":
        st.markdown("**:grey[Average Completion Rate by Hour]**")
        st.line_chart(comp_rate, x="Hour of Day", y="Avg Completion Rate", color="#5de488")

    else:
        st.markdown("**:grey[Average Skip Rate by Hour]**")
        st.line_chart(skip_rate, x="Hour of Day", y="Avg Skip Rate", color="#5de488")

# QUICK INSIGHTS

with col2:

    peak_hour = total_streams.loc[total_streams["Total Streams"].idxmax(), "Hour of Day"]
    peak_streams = total_streams["Total Streams"].max()
    peak_proportion = peak_streams / TOTAL_STREAMS

    # Convert peak_hour to 12-hour time
    def convert_hour_datetime(hour_24: int) -> str:
        return time(hour_24).strftime("%I %p").lstrip("0")

    # To show completion and skip rates are nearly flat:

    # Compute coefficient of variation (std dev / mean) across
    # all 24 hours for completion and skip rates
    cv_completion = comp_rate["Avg Completion Rate"].std() / comp_rate["Avg Completion Rate"].mean()
    cv_skip = skip_rate["Avg Skip Rate"].std() / skip_rate["Avg Skip Rate"].mean()

    # To show engagement quality remains stable regardless of time:

    # Compute Pearson correlation b/t hour of day and completion/skip rate
    # (to measure the strength & direction of their relationship)
    # r: correlation coefficient -- if close to 0 -> no meaningful relationship
    # p: p-value -- if high (above 0.05) -> no statistically significant relationship
    r_completion, p_completion = pearsonr(comp_rate["Hour of Day"].astype(float),
                                          comp_rate["Avg Completion Rate"].astype(float))

    r_skip, p_skip = pearsonr(skip_rate["Hour of Day"].astype(float),
                              skip_rate["Avg Skip Rate"].astype(float))

    st.markdown("##### :green[:material/Format_List_Bulleted:] Quick Insights")

    st.divider()
    col1, col2 = st.columns([0.5,5])

    col1.markdown(":green-badge[:material/Schedule:]")

    with col2:
        st.markdown(f""" **Peak hour** <br>
                        :grey[Streams peak at :green-badge[{convert_hour_datetime(int(peak_hour))}], making up
                        :green-badge[{(peak_proportion*100):.1f}%] of daily activity.
                        Activity clusters in two windows — mid-morning and evening.]
                    """, unsafe_allow_html=True)

    st.space("xxsmall")
    st.divider()

    col1, col2 = st.columns([0.5,5])

    col1.markdown(":green-badge[:material/Vital_Signs:]")

    with col2:
        st.markdown(""" **Completion & skip vs. time** <br>
                        :grey[Both rates are nearly flat across all 24 hours — engagement quality
                        is independent of time of day.]
                    """, unsafe_allow_html=True)

    st.space("xxsmall")

    with st.container(key="grey_container"):

        col1, col2 = st.columns([0.5,5])

        col1.markdown(":grey[:material/Info:]")

        with col2:
            st.markdown(""" **Limitation** <br>
                :grey[Completion rates weren't modeled from user tendencies;
                skip behavior was assigned independently of time.
                A future model could make both time-dependent.]
                        """, unsafe_allow_html=True)

with st.expander("**:grey[:material/Bar_Chart: Statistical backing]**"):
    col1, col2 = st.columns(2, border=True)

    col1.metric("Completion rate CV", f":green[{cv_completion:.3f}]")
    col1.caption("Low CV confirms near-flat distribution across hours")

    col2.metric("Skip rate CV", f":green[{cv_skip:.3f}]")
    col2.caption("Low CV confirms near-flat distribution across hours")

    col1, col2 = st.columns(2, border=True)

    col1.metric("Completion vs. hour (r)", f":green[{r_completion:.3f}]")
    col1.caption(f"p = {p_completion:.3f} — no significant time-of-day effect")

    col2.metric("Skip rate vs. hour (r)", f":green[{r_skip:.3f}]")
    col2.caption(f"p = {p_skip:.3f} — no significant time-of-day effect")


    with st.container(key="grey_container_3"):

        col1, col2 = st.columns([0.1,5])

        col1.markdown(":grey[:material/Info:]")

        with col2:
            st.markdown(""" **Why near-zero?** <br>
                :grey[Skip tendencies were assigned independently of
                time of day, and completion durations were generated randomly rather than drawn from
                user-level tendencies.]
                        """, unsafe_allow_html=True)


st.space("xxsmall")

st.html('<a name="user-behavior"></a>')

col1, col2 = st.columns([2,1], border=True)

with col1:
    # ** USER BEHAVIOR ANALYTICS **
    st.markdown("##### :green[:material/Repeat:] User Behavior Analytics")

    st.markdown(":grey[Each chart below shows the distribution of a given metric across the entire user base.]")

    # DISTRIBUTION HISTOGRAMS
    metric = st.pills("Metric",
                        [
                            "Streams Per Song",
                            "Skip Rate",
                            "Completion Rate",
                            "Diversity Score",
                            "Distinct Genres",
                            "Distinct Artists"
                        ],
                        default="Streams Per Song"
                        )

    st.space("xxsmall")

    # Get dataframe with the following columns:
    # "Skip Rate", "Avg Completion Rate", "Avg Streams Per Song"
    # "Distinct Genres", "Distinct Artists"
    df = get_behavior_data()
    skip_rate = df[["Skip Rate"]]
    comp_rate = df[["Avg Completion Rate"]]
    replay_rate = df[["Avg Streams Per Song"]]
    genres = df[["Distinct Genres"]]
    artists = df[["Distinct Artists"]]

    # Get dataframe with one "Diversity Score" column
    diversity_df = get_diversity_scores()

    if metric == "Skip Rate":
        # Create and display plotly histograms for each metric
        st.markdown("**:grey[Skip Rate Distribution]**")
        fig1 = px.histogram(skip_rate, x="Skip Rate", color_discrete_sequence=['#5de488'])
        st.plotly_chart(fig1)

    elif metric == "Completion Rate":
        st.markdown("**:grey[Completion Rate Distribution]**")
        fig2 = px.histogram(comp_rate, x="Avg Completion Rate", color_discrete_sequence=['#5de488'])
        st.plotly_chart(fig2)

    elif metric == "Streams Per Song":
        st.markdown("**:grey[Streams Per Song Distribution]**")
        fig3 = px.histogram(replay_rate, x="Avg Streams Per Song", color_discrete_sequence=['#5de488'])
        st.plotly_chart(fig3)
        st.caption("Shows how often users replay the same song on average, reflecting the " \
                   "depth of engagement with individual tracks. Users with a higher average streams " \
                   "per song tend to revisit the same songs repeatedly rather than consistently " \
                   "streaming new ones.")

    elif metric == "Diversity Score":
        st.markdown("**:grey[Diversity Score Distribution]**")
        fig4 = px.histogram(diversity_df, x="Diversity Score", color_discrete_sequence=['#5de488'])
        st.plotly_chart(fig4)
        st.caption("A user's diversity score measures how varied their listening taste " \
                "is across genres, accounting for both the number of genres streamed " \
                "and how evenly streams are distributed among them.")

        # Diversity Score Breakdown
        with st.expander(":green[Diversity Score Breakdown]"):
            # Diversity Score
            st.subheader("Diversity Score")
            st.write("""
                    **Diversity Score** $= 1 − \\sum (p_i^2)$\n
                    where $p_i$ is the proportion of a user's total streams belonging to genre $i$.\n
                    * Squaring each genre proportion penalizes dominance -- a genre that accounts for 80%
                    of streams contributes 0.64 to the sum, while one that accounts for 20% contributes only 0.04.
                    Subtracting from 1 flips the scale so that higher scores reflect greater diversity.\n
                    * A user whose streams are spread evenly across many genres will have small proportions
                    that sum to a low value, yielding a score close to 1. A user who streams almost exclusively
                    one genre will have one proportion close to 1, pushing the score close to 0.
                    """)
            st.markdown("#### Example:")
            st.write("""
                    * :green[User A]: &emsp; 90% Rock, 10% Pop &emsp; &emsp; &emsp; &emsp; &emsp; &emsp; &emsp;
                                                            &emsp; &ensp; &emsp; → &emsp; Diversity ≈ low
                    * :violet[User B]: &emsp; 25% Rock, 25% Pop, 25% Hip-Hop, 25% Jazz &emsp; → &emsp; Diversity ≈ high
                    """)

    elif metric == "Distinct Genres":
        st.markdown("**:grey[Distinct Genres Distribution]**")
        fig5 = px.histogram(genres, x="Distinct Genres", color_discrete_sequence=['#5de488'])
        st.plotly_chart(fig5)

    else:
        st.markdown("**:grey[Distinct Artists Distribution]**")
        fig6 = px.histogram(artists, x="Distinct Artists", color_discrete_sequence=['#5de488'])
        st.plotly_chart(fig6)

# QUICK INSIGHTS
with col2:

    # Get user behavior metrics view w/ where each row represents one user's metrics
    ubm_df = get_user_behavior_metrics()

    # Get avg streams per song (replays) -- (currently 2.4 streams / song)
    avg_replays = replay_rate["Avg Streams Per Song"].mean()

    # Get top 10% of users by stream count
    ten_percent_users = int(TOTAL_USERS * 0.1)
    top_listeners = ubm_df.nlargest(ten_percent_users, "total_streams")

    # Sum streams of top 10% users
    top_streams = top_listeners["total_streams"].sum()

    # Get proportion of total streams for top 10% of users
    top_streams_proportion = top_streams / TOTAL_STREAMS

    # Determine correlation b/t replay and skip rates
    # for users w/ above average replay rates:

    # Get users w/ above average replay rates
    replayers = ubm_df.loc[ubm_df["avg_streams_per_song"] > avg_replays]

    # Compute Pearson correlation b/t replay and skip rates for these users
    # (to measure the strength & direction of the potential relationship)
    # r: correlation coefficient -- if close to 0 -> no meaningful relationship
    # p: p-value -- if high (above 0.05) -> no statistically significant relationship
    r_replay, p_replay = pearsonr(replayers["avg_streams_per_song"].astype(float),
                            replayers["skip_rate"].astype(float))
    # Currently -- r_replay = -0.0347, p_replay = 0.641

    # Determine correlation b/t diversity and skip rates
    # for users w/ above average diversity scores:

    # Get users w/ above average diversity scores
    udm_df = get_user_diversity_metrics() # View where each row represents one user
    avg_diversity = udm_df["diversity_score"].mean()
    diverse_users = udm_df.loc[udm_df["diversity_score"] > avg_diversity]
    # Merge diverse users df with the users behavior metrics df to get diverse users' skip rates
    merged_df = diverse_users.merge(ubm_df, on="user_id")

    # Compute Pearson correlation b/t diversity scores and skip rates for these users
    # (to measure the strength & direction of the potential relationship)
    # r: correlation coefficient -- if close to 0 -> no meaningful relationship
    # p: p-value -- if high (above 0.05) -> no statistically significant relationship
    r_diversity, p_diversity = pearsonr(merged_df["diversity_score"].astype(float),
                            merged_df["skip_rate"].astype(float))
    # Currently -- r_diversity = -0.00448, p_diversity = 0.937

    st.markdown("##### :green[:material/Format_List_Bulleted:] Quick Insights")

    st.space("xxsmall")

    st.divider()

    # Replay rate
    col1, col2 = st.columns([0.5,5])
    with col1:
        st.markdown(":green-badge[:material/Repeat:]")
    with col2:
        st.markdown(f""" **Replay rate** <br>
                    :grey[The average user streams the same song :green-badge[{avg_replays:.1f}&times;],
                    suggesting moderate replay behavior across the platform.]
                    """, unsafe_allow_html=True)

    # Engagement split
    col1, col2 = st.columns([0.5,5])
    with col1:
        st.markdown(":green-badge[:material/Clock_Loader_20:]")
    with col2:
        st.markdown(f""" **Engagement split** <br>
                    :grey[The top 10% of users by stream count account for
                    :green-badge[{round(top_streams_proportion*100)}%] of total streams.]
                    """, unsafe_allow_html=True)

    # Replay vs. skip
    col1, col2 = st.columns([0.5,5])
    with col1:
        st.markdown(":green-badge[:material/Forward_Media:]")
    with col2:
        st.markdown(f""" **Replay vs. skip** <br>
                    :grey[No significant correlation — replay and skip tendencies are independent behaviors.]
                    """, unsafe_allow_html=True)

    # Diversity vs. skip
    col1, col2 = st.columns([0.5,5])
    with col1:
        st.markdown(":green-badge[:material/Grid_View:]")
    with col2:
        st.markdown(f""" **Diversity vs. skip** <br>
                    :grey[No significant correlation — genre exploration habits don't predict skip tendency.]
                    """, unsafe_allow_html=True)

    st.space("xxsmall")

    # Limitation
    with st.container(key="grey_container_2"):

        col1, col2 = st.columns([0.5,5])

        col1.markdown(":grey[:material/Info:]")

        with col2:
            st.markdown(""" **Limitation** <br>
                :grey[Skip, replay, and exploration tendencies were assigned independently
                during data generation. A future model could introduce dependencies between these traits.]
                        """, unsafe_allow_html=True)


with st.expander("**:grey[:material/Bar_Chart: Statistical backing]**"):
    col1, col2 = st.columns(2, border=True)

    col1.metric("Replay rate vs. skip rate (r)", f":green[{r_replay:.3f}]")
    col1.caption(f"p = {p_replay:.3f} — no significant correlation")

    col2.metric("Diversity score vs. skip rate (r)", f":green[{r_diversity:.3f}]")
    col2.caption(f"p = {p_diversity:.3f} — no significant correlation")

    with st.container(key="grey_container_4"):

        col1, col2 = st.columns([0.1,5])

        col1.markdown(":grey[:material/Info:]")

        with col2:
            st.markdown(""" **Scope** <br>
                :grey[Correlations were computed among users with above-average replay rates and
                above-average diversity scores respectively. The lack of significant results is
                expected — skip, replay, and exploration tendencies were assigned independently,
                so no behavioral correlations were embedded in the data.]
                        """, unsafe_allow_html=True)
