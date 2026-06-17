import sqlite3

DB_PATH = "/workspaces/music-streaming-project/db/music.db"
SCHEMA_PATH = "/workspaces/273640407/music_db_project/db/reset.sql"

def reset_db():
    conn = sqlite3.connect(DB_PATH)
    with open(SCHEMA_PATH, "r") as f:
        reset_sql = f.read()

    conn.executescript(reset_sql)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    reset_db()
    print("Database reset complete.")
