import pandas as pd
import csv

# Path to raw dataset csv
PATH = "/workspaces/273640407/music_db_project/raw_dataset.csv"

# Necessary columns from the Kaggle dataset
COLUMNS = [
    "track_id",
    "artists",
    "album_name",
    "track_name",
    "popularity",
    "duration_ms",
    "track_genre",
]

# Minimum level of popularity for a song to be extracted
MIN_POPULARITY = 70


# Expects path to raw spotify dataset csv:
# https://www.kaggle.com/datasets/maharshipandya/-spotify-tracks-dataset
# Reads dataset csv using pandas
# (columns limited to COLUMNS and rows with at least one NaN dropped)
# Returns dataframe
def load_data(path: str = PATH) -> pd.DataFrame:
    return pd.read_csv(path, usecols=COLUMNS).dropna()


# Expects the dataframe returned by load_data
# Extracts songs with one artist and a minimum popularity
# Returns a list of dicts, where each dict represents a track
def extract_tracks(df: pd.DataFrame) -> list[dict]:
    tracks = []

    # Iterate through rows to extract song data
    for row in df.itertuples():

        # Skip collaborations (multi-artist tracks) to simplify normalization
        # This avoids a many-to-many artist-track relationship at this stage
        if ";" in row.artists:
            continue

        # Check popularity
        if row.popularity < MIN_POPULARITY:
            continue

        # Create a dictionary for each song
        track = {
            "track_id": row.track_id,
            "artist": row.artists,
            "album": row.album_name,
            "track_name": row.track_name,
            "duration_ms": row.duration_ms,
            "track_genre": row.track_genre,
        }

        # Add song to list of songs
        tracks.append(track)

    return tracks


# Expects a list of tracks (as dicts)
# Returns a deduplicated list
def deduplicate(tracks: list[dict]) -> list[dict]:
    seen = set()
    unique_tracks = []

    # Ensure (track_name, artist) pairs are unique for
    # each track dictionary in the list
    for track in tracks:
        key = (track["track_name"].strip().lower(), track["artist"].strip().lower())

        if key not in seen:
            seen.add(key)
            unique_tracks.append(track)

    return unique_tracks


# Write song data to a new CSV file called "tracks.csv"
def write_csv(tracks, output_path="tracks.csv"):
    fieldnames = [
        "track_id",
        "artist",
        "album",
        "track_name",
        "duration_ms",
        "track_genre",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tracks)


# Builds cleaned dataset of tracks
def build_dataset():
    df = load_data(PATH)
    tracks = extract_tracks(df)
    unique_tracks = deduplicate(tracks)
    write_csv(unique_tracks)


if __name__ == "__main__":
    build_dataset()
