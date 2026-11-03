import requests
import pandas as pd
import time
from datetime import datetime, timezone


# ============================================================
# SETTINGS
# ============================================================

# Input file created by the post scraper
INPUT_FILE = "melbourne_suburb_posts_2021_present.csv"

# Output containing every collected comment
OUTPUT_ALL = "melbourne_suburb_comments.csv"

# Output containing only comments that explicitly
# mention the suburb being analysed
OUTPUT_MATCHING = "melbourne_suburb_matching_comments.csv"

BASE_URL = "https://arctic-shift.photon-reddit.com"

COMMENT_TREE_URL = f"{BASE_URL}/api/comments/tree"

# Maximum number of comments requested for each post
COMMENT_LIMIT = 9999

# Delay between API requests
REQUEST_DELAY = 2


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

    for attempt in range(retries):

        try:

            response = session.get(
                url,
                params=params,
                timeout=60
            )

            # --------------------------------------------
            # RATE LIMITED
            # --------------------------------------------

            if response.status_code == 429:

                print(
                    "Rate limited. "
                    "Waiting 10 seconds..."
                )

                time.sleep(10)

                continue

            # --------------------------------------------
            # ARCTIC SHIFT TIMEOUT
            # --------------------------------------------

            if response.status_code == 422:

                try:

                    error_message = (
                        response.json().get(
                            "error",
                            ""
                        )
                    )

                except Exception:

                    error_message = (
                        response.text
                    )

                # Arctic Shift sometimes returns
                # status 422 when a query takes too long
                if "Timeout" in error_message:

                    wait_time = (
                        10 * (attempt + 1)
                    )

                    print(
                        f"Request timed out. "
                        f"Waiting {wait_time} seconds..."
                    )

                    time.sleep(
                        wait_time
                    )

                    continue

            # Raise error for other bad responses
            response.raise_for_status()

            return response.json()

        except Exception as e:

            print(
                f"Request failed "
                f"(attempt {attempt + 1}/{retries}): "
                f"{e}"
            )

            time.sleep(5)

    return None


# ============================================================
# DATE CONVERTER
# ============================================================

def convert_date(timestamp):

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
# LOAD POSTS DATASET
# ============================================================

posts_df = pd.read_csv(
    INPUT_FILE
)

print(
    f"Posts loaded: "
    f"{len(posts_df)}"
)


# Store all collected comments
comment_rows = []


# ============================================================
# FLATTEN COMMENT TREE
# ============================================================

def flatten_comments(
    nodes,
    suburb,
    post_id,
    post_title,
    post_url,
    subreddit,
    depth=0
):
    """
    Convert the nested Reddit comment tree
    into individual rows.

    The function also recursively processes
    replies to comments.
    """

    # Make sure nodes is a list
    if not isinstance(nodes, list):
        return

    # Process each comment node
    for node in nodes:

        # Ignore invalid nodes
        if not isinstance(node, dict):
            continue


        # --------------------------------------------
        # IGNORE "MORE" PLACEHOLDERS
        # --------------------------------------------

        # Reddit sometimes includes a "more" object
        # instead of an actual comment
        if node.get("kind") == "more":
            continue


        # --------------------------------------------
        # GET COMMENT DATA
        # --------------------------------------------

        # The actual Reddit comment information
        # is stored inside node["data"]
        comment = node.get(
            "data",
            {}
        )

        if not isinstance(comment, dict):
            continue


        # Get comment ID
        comment_id = comment.get(
            "id"
        )

        # Get comment text
        body = comment.get(
            "body",
            ""
        )


        # --------------------------------------------
        # SAVE COMMENT
        # --------------------------------------------

        if comment_id:

            permalink = comment.get(
                "permalink"
            )

            # Create full Reddit comment URL
            if permalink:

                comment_url = (
                    "https://www.reddit.com"
                    + permalink
                )

            else:

                comment_url = None


            # Check whether the comment explicitly
            # contains the suburb name
            contains_suburb = (
                suburb.lower()
                in str(body).lower()
            )


            comment_rows.append({

                # Suburb associated with the original search
                "suburb":
                    suburb,

                # Original Reddit post ID
                "post_id":
                    post_id,

                # Unique Reddit comment ID
                "comment_id":
                    comment_id,

                # Original post title
                "post_title":
                    post_title,

                # Subreddit where the post appeared
                "subreddit":
                    subreddit,

                # Comment text
                "comment_content":
                    body,

                # Comment creation date
                "comment_date_utc":
                    convert_date(
                        comment.get(
                            "created_utc"
                        )
                    ),

                # Reddit comment score
                "comment_score":
                    comment.get(
                        "score"
                    ),

                # ID of the parent post/comment
                "parent_id":
                    comment.get(
                        "parent_id"
                    ),

                # Depth in the reply tree
                "comment_depth":
                    depth,

                # Reddit username
                "author":
                    comment.get(
                        "author"
                    ),

                # Whether the commenter
                # created the original post
                "is_submitter":
                    comment.get(
                        "is_submitter"
                    ),

                # Reddit controversiality value
                "controversiality":
                    comment.get(
                        "controversiality"
                    ),

                # Whether the comment was edited
                "edited":
                    comment.get(
                        "edited"
                    ),

                # Whether the suburb name appears
                # directly inside the comment
                "contains_suburb":
                    contains_suburb,

                # Original post URL
                "post_url":
                    post_url,

                # Direct comment URL
                "comment_url":
                    comment_url
            })


        # --------------------------------------------
        # NESTED REPLIES
        # --------------------------------------------

        # Replies are stored inside:
        #
        # replies
        #   -> data
        #       -> children

        replies = comment.get(
            "replies"
        )


        if isinstance(
            replies,
            dict
        ):

            reply_data = replies.get(
                "data",
                {}
            )

            if isinstance(
                reply_data,
                dict
            ):

                children = reply_data.get(
                    "children",
                    []
                )

                if isinstance(
                    children,
                    list
                ):

                    # Recursively process replies
                    flatten_comments(
                        children,
                        suburb,
                        post_id,
                        post_title,
                        post_url,
                        subreddit,
                        depth + 1
                    )


# ============================================================
# PROCESS ALL POSTS
# ============================================================

for index, post in posts_df.iterrows():


    # --------------------------------------------
    # GET POST INFORMATION
    # --------------------------------------------

    post_id = str(
        post["post_id"]
    )

    suburb = str(
        post.get(
            "suburb",
            ""
        )
    )

    post_title = post.get(
        "post_title",
        ""
    )

    post_url = post.get(
        "post_url",
        ""
    )


    # Your new post dataset uses
    # searched_subreddit
    subreddit = post.get(
        "searched_subreddit",
        ""
    )


    print(
        f"{index + 1}/{len(posts_df)} "
        f"{suburb} | "
        f"r/{subreddit} | "
        f"Post: {post_id}"
    )


    # --------------------------------------------
    # REQUEST COMMENT TREE
    # --------------------------------------------

    response = request_json(
        COMMENT_TREE_URL,
        {
            "link_id":
                f"t3_{post_id}",

            "limit":
                COMMENT_LIMIT
        }
    )


    # --------------------------------------------
    # NO RESPONSE
    # --------------------------------------------

    if response is None:

        print(
            "  No response"
        )

        continue


    # --------------------------------------------
    # GET COMMENT TREE
    # --------------------------------------------

    # Arctic Shift returns:
    #
    # {
    #     "data": [...]
    # }

    tree = response.get(
        "data",
        []
    )


    # Number of comments before
    # processing this post
    before = len(
        comment_rows
    )


    # Flatten the nested comment tree
    flatten_comments(
        tree,
        suburb,
        post_id,
        post_title,
        post_url,
        subreddit
    )


    # Calculate how many comments
    # were added for this post
    retrieved = (
        len(comment_rows)
        - before
    )


    print(
        f"  Retrieved: "
        f"{retrieved} comments"
    )


    # Wait before requesting
    # the next post
    time.sleep(
        REQUEST_DELAY
    )


# ============================================================
# CREATE DATAFRAME
# ============================================================

comments_df = pd.DataFrame(
    comment_rows
)


# ============================================================
# REMOVE DUPLICATE COMMENTS
# ============================================================

if not comments_df.empty:

    comments_df.drop_duplicates(
        subset=[
            "comment_id"
        ],
        inplace=True
    )

    comments_df.reset_index(
        drop=True,
        inplace=True
    )


# ============================================================
# SAVE ALL COMMENTS
# ============================================================

comments_df.to_csv(
    OUTPUT_ALL,
    index=False
)


# ============================================================
# SAVE COMMENTS THAT EXPLICITLY MENTION SUBURB
# ============================================================

if not comments_df.empty:

    matching_df = comments_df[
        comments_df[
            "contains_suburb"
        ] == True
    ].copy()

else:

    matching_df = pd.DataFrame()


matching_df.to_csv(
    OUTPUT_MATCHING,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n========================================")
print("COMMENT COLLECTION FINISHED")
print("========================================")


print(
    f"Posts processed: "
    f"{len(posts_df)}"
)

print(
    f"Unique comments collected: "
    f"{len(comments_df)}"
)

print(
    f"Comments explicitly mentioning "
    f"their suburb: "
    f"{len(matching_df)}"
)


# ============================================================
# COMMENTS BY SUBURB
# ============================================================

if not comments_df.empty:

    print("\nCOMMENTS BY SUBURB")
    print("----------------------------------------")

    suburb_summary = (
        comments_df
        .groupby(
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
# COMMENTS BY SUBREDDIT
# ============================================================

if not comments_df.empty:

    print("\nCOMMENTS BY SUBREDDIT")
    print("----------------------------------------")

    subreddit_summary = (
        comments_df
        .groupby(
            "subreddit"
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
# SUBURB x SUBREDDIT SUMMARY
# ============================================================

if not comments_df.empty:

    print("\nCOMMENTS BY SUBURB AND SUBREDDIT")
    print("----------------------------------------")

    suburb_subreddit_summary = (
        comments_df
        .groupby(
            [
                "suburb",
                "subreddit"
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
# MATCHING COMMENTS BY SUBURB
# ============================================================

if not matching_df.empty:

    print("\nCOMMENTS EXPLICITLY MENTIONING SUBURB")
    print("----------------------------------------")

    matching_summary = (
        matching_df
        .groupby(
            "suburb"
        )
        .size()
        .sort_values(
            ascending=False
        )
    )

    print(
        matching_summary
    )


# ============================================================
# FILES CREATED
# ============================================================

print("\nFiles created:")

print(
    OUTPUT_ALL
)

print(
    OUTPUT_MATCHING
)