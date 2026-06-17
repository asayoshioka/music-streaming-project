import sqlite3
import random
import numpy as np
from datetime import datetime, timedelta, time
from faker import Faker

DB_PATH = "/workspaces/273640407/music_db_project/db/music.db"

random.seed(42)
np.random.seed(42)

fake = Faker()

NUM_USERS = 500

# Top 15 countries that use Spotify, according to Google's AI
COUNTRIES = [
    "US",
    "BR",
    "GB",
    "MX",
    "IN",
    "DE",
    "CA",
    "FR",
    "ES",
    "AU",
    "IT",
    "SE",
    "NL",
    "JP",
    "AR",
]

# Probabilities for each country (used in the generate_users function below)
# Roughly based on Spotify stats, e.g. the U.S. comprises 30% of Spotify users.
COUNTRIES_WEIGHTS = [
    0.3,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05,
    0.05
]

SUBSCRIPTIONS = ["free", "premium"]

# Based on Spotify stats -- 60% of users are FREE
SUBSCRIPTIONS_WEIGHTS = [0.6, 0.4]

PLATFORM_LAUNCH = datetime(2020, 1, 1)


# Generates a random datetime between the platform's launch and
# at latest two years ago.
def random_datetime(start: datetime = PLATFORM_LAUNCH, end: datetime = None) -> str:

    """
    Returns a random string ("YYYY-MM-DD hh:mm:ss") between two datetime objects
    """

    # Default end to two years ago from the current date.
    # (This is to support the stream generation model, which biases recent dates.
    # This ensures streams are not generated after a user's signup date.)
    if end is None:
        end = datetime.combine(datetime.now() - timedelta(days=730), time.min)

    # Calculate the total seconds between start and end
    delta = int((end - start).total_seconds())

    # Generate a random number of seconds between 0 and delta
    rand_secs = random.randint(0, delta)

    # Convert rand_secs to a timedelta object and add to start
    secs = timedelta(seconds=rand_secs)

    rand_date = start + secs

    return rand_date.strftime("%Y-%m-%d %H:%M:%S")


# Expects an integer n
# Generates a list with n tuples of the form
# (username, country, subscription_type, signup_date)
def generate_users(n) -> list:

    users = []

    try:
        for _ in range(n):
            username = fake.unique.user_name()
            country = np.random.choice(COUNTRIES, p=COUNTRIES_WEIGHTS)
            subscription = np.random.choice(SUBSCRIPTIONS, p=SUBSCRIPTIONS_WEIGHTS)
            signup_date = random_datetime()
            user = (username, country, subscription, signup_date)
            users.append(user)

        return users

    except TypeError:
        raise


# Expects a list of user data, where each
# element is a tuple of the following form:
# (username, country, subscription_type, signup_date)
# Inserts the tuples into the "users" table in music.db
def insert_users(users):

    try:

        with sqlite3.connect(DB_PATH) as con:

            cur = con.cursor()

            cur.executemany(
                """
                INSERT INTO "users" ("username", "country", "subscription_type", "signup_date")
                VALUES (?, ?, ?, ?)
                """,
                users,
            )

            con.commit()
            
        # Return the number of users successfully seeded
        return len(users)

    except sqlite3.Error as e:
        raise e


# Seeds n random users in "users" within music.db
def seed_users(n):
    num_users = insert_users(generate_users(n))
    print(f"{num_users} users seeded.")


if __name__ == "__main__":
    seed_users(NUM_USERS)

