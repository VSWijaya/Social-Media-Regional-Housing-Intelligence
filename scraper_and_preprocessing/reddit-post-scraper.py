import requests
import pandas as pd
import time
from datetime import datetime, timezone


# ============================================================
# SETTINGS
# ============================================================

SUBURBS = [
    "Collingwood",
    "Oakleigh",
    "Nunawading",
    "Eaglemont",
    "Richmond",
    "Carlton",
    "Vermont",
    "Dandenong",
    "Officer",
    "Clayton"
]

SUBREDDITS = [
    "melbourne",
    "AusProperty",
    "AusPropertyChat",
    "AusFinance",
    "AskAnAustralian"
]

BASE_URL = "https://arctic-shift.photon-reddit.com"

POST_SEARCH = f"{BASE_URL}/api/posts/search"

OUTPUT_FILE = "melbourne_suburb_posts_2021_present.csv"

# Start from 2021 to broadly align with the 2021 ABS Census
START_DATE = "2021-01-01"

# Maximum number of posts requested per API call
REQUEST_LIMIT = 100

# Delay between requests
REQUEST_DELAY = 10


# ============================================================
# HTTP SESSION
# ============================================================

session = requests.Session()

session.headers.update({
    "User-Agent": "melbourne-suburb-research-project/1.0"
})


# ============================================================
# REQUEST HELPER
# ============================================================

def request_json(url, params=None, retries=4):
    """
    Send a GET request to the API.

    If the request fails or is rate limited,
    retry several times before giving up.
    """

    for attempt in range(retries):

        try:

            response = session.get(
                url,
                params=params,
                timeout=60
            )

            # --------------------------------------------
            # RATE LIMIT
            # --------------------------------------------

            if response.status_code == 429:

                print(
                    "Rate limited. "
                    "Waiting 10 seconds..."
                )

                time.sleep(10)

                continue

            # --------------------------------------------
            # ARCTIC SHIFT SEARCH TIMEOUT
            # --------------------------------------------

            if response.status_code == 422:

                try:
                    error_message = response.json().get(
                        "error",
                        ""
                    )
                except Exception:
                    error_message = response.text

                # Arctic Shift sometimes returns 422
                # when the search takes too long
                if "Timeout" in error_message:

                    wait_time = 10 * (attempt + 1)

                    print(
                        f"Search timed out. "
                        f"Waiting {wait_time} seconds "
                        f"before retrying..."
                    )

                    time.sleep(wait_time)

                    continue

            # Raise error for bad HTTP responses
            response.raise_for_status()

            return response.json()

        except Exception as e:

            print(
                f"Request failed "
                f"(attempt {attempt + 1}/{retries}): "
                f"{e}"
            )

            time.sleep(3)

    return None


# ============================================================
# DATE CONVERTER
# ============================================================

def convert_date(timestamp):
    """
    Convert Reddit Unix timestamp
    into ISO-format UTC date.
    """

    if timestamp is None:
        return None

    try:

        return datetime.fromtimestamp(
            float(timestamp),
            timezone.utc
        ).isoformat()

    except Exception:

        return None


# ============================================================
# SEARCH POSTS FOR ONE SUBURB + ONE SUBREDDIT
# ============================================================

def search_posts(suburb, subreddit):
    """
    Search all Reddit posts containing one suburb name
    inside one subreddit.

    Uses timestamp-based pagination until
    no more posts are available.
    """

    # Store all posts collected for this suburb/subreddit
    all_posts = []

    # Start searching from the selected start date
    after = START_DATE

    # Control whether another page should be requested
    keep_searching = True

    print("\n========================================")
    print(f"Searching suburb: {suburb}")
    print(f"Subreddit: r/{subreddit}")
    print("========================================")

    # Continue while there may still be posts to retrieve
    while keep_searching:

        print(
            f"Searching after: {after}"
        )

        # --------------------------------------------
        # SEARCH PARAMETERS
        # --------------------------------------------

        params = {

            # Search only inside the selected subreddit
            "subreddit": subreddit,

            # Search for the suburb name
            "query": suburb,

            # Only return posts created after this point
            "after": after,

            # Return posts from oldest to newest
            "sort": "asc",

            # Maximum number of posts per request
            "limit": REQUEST_LIMIT
        }

        # Send request to Arctic Shift API
        response = request_json(
            POST_SEARCH,
            params=params
        )

        # --------------------------------------------
        # REQUEST FAILED
        # --------------------------------------------

        # Stop searching if the request fails
        if response is None:

            print(
                "Request failed completely."
            )

            keep_searching = False

            continue

        # --------------------------------------------
        # GET POSTS
        # --------------------------------------------

        # Extract posts from the API response
        batch = response.get(
            "data",
            []
        )

        # Stop searching if no posts are returned
        if not batch:

            print(
                "No more posts found."
            )

            keep_searching = False

            continue

        # Display number of posts retrieved
        print(
            f"Retrieved {len(batch)} posts"
        )

        # Add current posts to the complete list
        all_posts.extend(
            batch
        )

        # --------------------------------------------
        # GET NEWEST TIMESTAMP
        # --------------------------------------------

        # Get the creation timestamp from each post
        timestamps = [
            post.get("created_utc")
            for post in batch
            if post.get("created_utc") is not None
        ]

        # Stop if timestamps are unavailable
        if not timestamps:

            print(
                "No valid timestamps found."
            )

            keep_searching = False

            continue

        # Find the newest post in the current batch
        newest_timestamp = max(
            float(timestamp)
            for timestamp in timestamps
        )

        # Start the next request one second after
        # the newest post from the current batch
        after = str(
            int(newest_timestamp) + 1
        )

        # --------------------------------------------
        # CHECK IF FINAL PAGE
        # --------------------------------------------

        # If fewer than REQUEST_LIMIT posts are returned,
        # assume there are no more pages
        if len(batch) < REQUEST_LIMIT:

            print(
                "Reached final page."
            )

            keep_searching = False

        # --------------------------------------------
        # REQUEST DELAY
        # --------------------------------------------

        # Wait before making the next API request
        if keep_searching:

            time.sleep(
                REQUEST_DELAY
            )

    # Return all collected posts
    return all_posts


# ============================================================
# SEARCH ALL SUBURBS + SUBREDDITS
# ============================================================

all_results = []

total_searches = (
    len(SUBURBS)
    * len(SUBREDDITS)
)

current_search = 0


for suburb in SUBURBS:

    for subreddit in SUBREDDITS:

        current_search += 1

        print("\n\n")
        print(
            f"SEARCH "
            f"{current_search}/"
            f"{total_searches}"
        )

        print(
            f"{suburb} "
            f"→ r/{subreddit}"
        )

        posts = search_posts(
            suburb,
            subreddit
        )

        # --------------------------------------------
        # ADD SEARCH INFORMATION TO EACH POST
        # --------------------------------------------

        for post in posts:

            post[
                "_searched_suburb"
            ] = suburb

            post[
                "_searched_subreddit"
            ] = subreddit

            all_results.append(
                post
            )

        time.sleep(
            REQUEST_DELAY
        )


# ============================================================
# FORMAT OUTPUT
# ============================================================

rows = []


for post in all_results:

    post_id = post.get(
        "id"
    )

    # Ignore records without an ID
    if not post_id:
        continue

    suburb = post.get(
        "_searched_suburb",
        ""
    )

    searched_subreddit = post.get(
        "_searched_subreddit",
        ""
    )

    title = post.get(
        "title",
        ""
    )

    content = post.get(
        "selftext",
        ""
    )

    permalink = post.get(
        "permalink",
        ""
    )

    # Make sure text values are strings
    title_text = str(
        title or ""
    )

    content_text = str(
        content or ""
    )

    suburb_lower = suburb.lower()

    # --------------------------------------------
    # CHECK WHERE SUBURB NAME APPEARS
    # --------------------------------------------

    keyword_in_title = (
        suburb_lower
        in title_text.lower()
    )

    keyword_in_content = (
        suburb_lower
        in content_text.lower()
    )

    # --------------------------------------------
    # CREATE FULL REDDIT URL
    # --------------------------------------------

    if permalink:

        post_url = (
            "https://www.reddit.com"
            + permalink
        )

    else:

        post_url = None

    # --------------------------------------------
    # CREATE CLEAN ROW
    # --------------------------------------------

    rows.append({

        "suburb":
            suburb,

        "searched_subreddit":
            searched_subreddit,

        "post_id":
            post_id,

        "post_title":
            title,

        "post_content":
            content,

        "post_date_utc":
            convert_date(
                post.get(
                    "created_utc"
                )
            ),

        "actual_subreddit":
            post.get(
                "subreddit"
            ),

        "post_score":
            post.get(
                "score"
            ),

        "num_comments":
            post.get(
                "num_comments"
            ),

        "post_url":
            post_url,

        "author":
            post.get(
                "author"
            ),

        "link_flair":
            post.get(
                "link_flair_text"
            ),

        "keyword_in_title":
            keyword_in_title,

        "keyword_in_content":
            keyword_in_content,

    })


# ============================================================
# CREATE PANDAS DATAFRAME
# ============================================================

df = pd.DataFrame(
    rows
)


# ============================================================
# REMOVE DUPLICATES
# ============================================================

if not df.empty:

    df.drop_duplicates(
        subset=[
            "suburb",
            "searched_subreddit",
            "post_id"
        ],
        inplace=True
    )


# ============================================================
# SORT DATA
# ============================================================

if not df.empty:

    df.sort_values(
        by=[
            "suburb",
            "post_date_utc"
        ],
        inplace=True
    )


# ============================================================
# RESET INDEX
# ============================================================

if not df.empty:

    df.reset_index(
        drop=True,
        inplace=True
    )


# ============================================================
# SAVE CSV
# ============================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n")
print("========================================")
print("SCRAPING COMPLETE")
print("========================================")

print(
    f"Total records collected: "
    f"{len(df)}"
)

print(
    f"Number of suburbs: "
    f"{len(SUBURBS)}"
)

print(
    f"Number of subreddits: "
    f"{len(SUBREDDITS)}"
)

print(
    f"Total search combinations: "
    f"{total_searches}"
)

print(
    f"Start date: "
    f"{START_DATE}"
)

print(
    f"\nSaved to: "
    f"{OUTPUT_FILE}"
)


# ============================================================
# SUMMARY BY SUBURB
# ============================================================

if not df.empty:

    print("\n")
    print(
        "POSTS BY SUBURB"
    )

    print(
        "----------------------------------------"
    )

    suburb_summary = (
        df.groupby(
            "suburb"
        )
        .size()
        .sort_values(
            ascending=False
        )
    )

    print(
        suburb_summary
    )


# ============================================================
# SUMMARY BY SUBREDDIT
# ============================================================

if not df.empty:

    print("\n")
    print(
        "POSTS BY SUBREDDIT"
    )

    print(
        "----------------------------------------"
    )

    subreddit_summary = (
        df.groupby(
            "searched_subreddit"
        )
        .size()
        .sort_values(
            ascending=False
        )
    )

    print(
        subreddit_summary
    )


# ============================================================
# SUBURB × SUBREDDIT TABLE
# ============================================================

if not df.empty:

    print("\n")
    print(
        "POSTS BY SUBURB AND SUBREDDIT"
    )

    print(
        "----------------------------------------"
    )

    suburb_subreddit_summary = (
        df.groupby(
            [
                "suburb",
                "searched_subreddit"
            ]
        )
        .size()
        .unstack(
            fill_value=0
        )
    )

    print(
        suburb_subreddit_summary
    )


# ============================================================
# NUMBER OF COMMENTS AVAILABLE
# ============================================================

if not df.empty:

    print("\n")
    print(
        "TOTAL COMMENT COUNTS BY SUBURB"
    )

    print(
        "----------------------------------------"
    )

    comment_summary = (
        df.groupby(
            "suburb"
        )[
            "num_comments"
        ]
        .sum()
        .sort_values(
            ascending=False
        )
    )

    print(
        comment_summary
    )


# ============================================================
# KEYWORD LOCATION SUMMARY
# ============================================================

if not df.empty:

    print("\n")
    print(
        "KEYWORD MATCH SUMMARY"
    )

    print(
        "----------------------------------------"
    )

    print(
        f"Suburb name in title: "
        f"{df['keyword_in_title'].sum()}"
    )

    print(
        f"Suburb name in post content: "
        f"{df['keyword_in_content'].sum()}"
    )


# ============================================================
# PREVIEW
# ============================================================

if not df.empty:

    print("\n")
    print(
        "DATA PREVIEW"
    )

    print(
        "----------------------------------------"
    )

    print(
        df[
            [
                "suburb",
                "searched_subreddit",
                "post_id",
                "post_title",
                "post_date_utc",
                "post_score",
                "num_comments",
                "post_url"
            ]
        ].head(20)
    )

else:

    print(
        "\nNo posts were collected."
    )