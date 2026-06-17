import streamlit as st
import sqlite3
from utils.queries import count_rows
from utils.get_ids_and_maps import get_user_ids


user_ids = get_user_ids()

# PAGE TITLE AND LAYOUT
st.set_page_config(page_title="Music Analytics | Asa",
                   page_icon="🎧", layout="wide")

# HEADER
st.header(":green[:material/Headphones:] Music Recommendation & Analytics")
st.write(":grey[A Spotify-inspired platform built with Python, SQLite, and Streamlit — by Asa Yoshioka]")
st.markdown(":grey-badge[Collaborative filtering] :grey-badge[User profiling] :grey-badge[SQL] :grey-badge[Streamlit] :grey-badge[ETL pipeline]")

st.space("xsmall")

# QUICK METRICS
col1, col2, col3, col4, col5 = st.columns(5, border=True)

# Get total users
total_users = count_rows("users")
# Get total streams
total_streams = count_rows("streams")
# Get total artists
total_artists = count_rows("artists")
# Get total songs
total_songs = count_rows("songs")
# Get total genres
total_genres = count_rows("genres")

col1.metric(":grey[**:grey[:material/Music_Note:] SONGS**]", f"**:green[{total_songs/1000:.1f}k]**")
col2.metric(":grey[**:grey[:material/Mic:] ARTISTS**]", f"**:green[{total_artists/1000:.1f}k]**")
col3.metric(":grey[**:grey[:material/Group:] USERS**]", f"**:green[{total_users}]**")
col4.metric(":grey[**:grey[:material/Play_Arrow:] STREAMS**]", f"**:green[{total_streams/1000:.1f}k]**")
col5.metric(":grey[**:grey[:material/Sell:] GENRES**]", f"**:green[{total_genres}]**")

st.caption("Songs and artists sourced from real Spotify metadata. Users, streams, and archetypes are synthetically generated.")

kaggle_url = "https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset"

# REMOVED -- PROJECT OVERVIEW
# with st.container(border=True):
    # st.markdown("##### :green[:material/Overview: Project Overview]")

    # st.write(f"""
    # :grey[This project is a Spotify-inspired music recommendation and analytics platform
    # built using Python, SQLite, SQL, and Streamlit.]

    # :grey[The system combines relational database design, ETL pipelines, synthetic
    # behavioral data generation, recommendation algorithms, user profiling,
    # and interactive dashboards.]

    # :grey[Music metadata was sourced from a [Spotify Tracks Dataset]({kaggle_url}) and loaded into a
    # normalized SQLite database. Synthetic users and listening activity were then
    # generated to simulate realistic streaming behavior, enabling the construction
    # of recommendation systems, user taste profiles, listener archetypes, and
    # platform-wide analytics.]

    # :grey[The goal of this project was to gain hands-on experience building a complete
    # data pipeline—from raw data ingestion to analytics and recommendation
    # interfaces—while developing practical SQL and Python skills.]
    # """)

st.divider()

st.markdown(":grey[**ABOUT THIS PROJECT**]")
st.markdown(f"""
This platform combines relational database design, ETL pipelines, synthetic behavioral data generation,
recommendation algorithms, user profiling, and interactive dashboards. Music metadata was sourced from
a [Spotify Tracks Dataset]({kaggle_url}) and loaded into a normalized SQLite database, with synthetic users and listening
activity generated to simulate realistic streaming behavior.
            """)

# with st.expander("**:grey[:material/Format_List_Bulleted: KEY FEATURES]**"):

#     st.markdown("""
#     * Collaborative filtering recommendation engine
#     * Listener archetype classification
#     * Genre and artist affinity scoring
#     * Explainable recommendations
#     * User-to-user similarity scoring
#     * Interactive Streamlit dashboards
#     * SQL view-based analytics architecture
#     """)

st.divider()

st.markdown("**:grey[TECH STACK]**")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True, height=185):
        st.markdown("""
        #### :green[:material/Database:]
        ##### Database
        :grey-badge[SQLite]
        :grey-badge[Schema design]
        :grey-badge[SQL views]
        :grey-badge[Junction tables]
        """)

with col2:
    with st.container(border=True, height=185):
        st.markdown("""
        #### :green[:material/Code_Xml:]
        ##### Data engineering
        :grey-badge[Python]
        :grey-badge[Pandas]
        :grey-badge[ETL pipelines]
        :grey-badge[Synthetic data]
        """)

with col3:
    with st.container(border=True, height=185):
        st.markdown("""
        #### :green[:material/Bar_Chart:]
        ##### Analytics & app
        :grey-badge[Streamlit]
        :grey-badge[Data viz]
        :grey-badge[Collab. filtering]
        :grey-badge[User profiling]
        :grey-badge[Rec. Systems]
        """)

st.divider()

st.markdown("**:grey[ARCHITECTURE SUMMARY]**")

st.write("A visual overview of the project pipeline — from raw data to interactive dashboard.")

col1, col2, col3 = st.columns([1, 10, 1])

col2.image("assets/data_pipeline_flowchart_horizontal_wrap.svg", width=700)

st.caption("Diagram created with Claude.")

st.divider()

st.markdown("**:grey[EXPLORE THE APPLICATION]**")

col_a, col_b = st.columns(2)
with col_a:
    with st.container(border=True, height=190):
        name_col, feat_col = st.columns([5,1])
        name_col.markdown("##### :green[:material/Stars_2:] Recommendation explorer")
        feat_col.markdown(":green-badge[Featured]")
        st.write(":grey[Personalized recommendations with explainable reasoning behind each suggestion.]")
        if st.button("Open :material/Arrow_Outward:", key="btn_5"):
            st.switch_page("pages/2_Recommendation_Explorer.py")
with col_b:
    with st.container(border=True, height=190):
        name_col, feat_col = st.columns([5,1])
        name_col.markdown("##### :green[:material/Group:] User similarity")
        feat_col.markdown(":green-badge[Featured]")
        st.write(":grey[Compare users based on listening overlap and shared musical tastes.]")
        if st.button("Open :material/Arrow_Outward:", key="btn_3"):
            st.switch_page("pages/3_User_Similarity_Explorer.py")

col1, col2, col3 = st.columns(3)

with col1:
    with st.container(border=True, height=210):
        st.markdown("##### :green[:material/Account_Circle:] User taste profiles")
        st.write(":grey[Listening habits, top genres, top artists, affinity scores, and listener archetypes for any user.]")
        if st.button("Open :material/Arrow_Outward:", key="btn_1"):
            st.switch_page("pages/1_User_Taste_Profiles.py")
    with st.container(border=True, height=190):
        st.markdown("##### :green[:material/Database:] Database & ETL")
        st.write(":grey[Relational schema, ETL pipeline, and the synthetic data generation process.]")
        if st.button("Open :material/Arrow_Outward:", key="btn_7"):
            st.switch_page("pages/6_Database_&_ETL.py")

with col2:
    with st.container(border=True, height=210):
        st.markdown("##### :green[:material/Equalizer:] Music analytics")
        st.write(":grey[Platform-wide listening trends, engagement metrics, top content, and listening behavior.]")
        if st.button("Open :material/Arrow_Outward:", key="btn_2"):
            st.switch_page("pages/4_Music_Analytics.py")
    with st.container(border=True, height=190):
        st.markdown("##### :green[:material/Code_Blocks:] SQL & analytics")
        st.write(":grey[SQL views, recommendation queries, and scoring systems that power the platform.]")
        if st.button("Open :material/Arrow_Outward:", key="btn_4"):
            st.switch_page("pages/7_SQL_&_Analytics_Engineering.py")

with col3:
    with st.container(border=True, height=210):
        st.markdown("##### :green[:material/Sell:] Listener archetypes")
        st.write(":grey[Classifications like Explorer, Focused Listener, Genre Loyalist, and more.]")
        if st.button("Open :material/Arrow_Outward:", key="btn_6"):
            st.switch_page("pages/5_Listener_Archetypes.py")
