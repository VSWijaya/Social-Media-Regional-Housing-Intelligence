import pandas as pd


# ============================================================
# FILE SETTINGS
# ============================================================

POST_FILE = "melbourne_suburb_posts_2021_present.csv"

COMMENT_FILE = "melbourne_suburb_comments.csv"

OUTPUT_FILE = "melbourne_suburb_master_dataset.csv"


# ============================================================
# LOAD DATASETS
# ============================================================

posts_df = pd.read_csv(
    POST_FILE
)

comments_df = pd.read_csv(
    COMMENT_FILE
)


print(
    f"Posts loaded: {len(posts_df)}"
)

print(
    f"Comments loaded: {len(comments_df)}"
)


# ============================================================
# CHECK COLUMN NAMES
# ============================================================

# Display the available columns so we can confirm
# that both datasets contain the expected fields.
print("\nPost columns:")
print(
    posts_df.columns.tolist()
)

print("\nComment columns:")
print(
    comments_df.columns.tolist()
)


# ============================================================
# STANDARDISE POST ID
# ============================================================

# Convert post_id to string in both datasets.
# This ensures the merge key has the same data type.
posts_df["post_id"] = (
    posts_df["post_id"]
    .astype(str)
)

comments_df["post_id"] = (
    comments_df["post_id"]
    .astype(str)
)


# ============================================================
# PREPARE POST CONTEXT
# ============================================================

# The comment dataset already contains:
# - post_title
# - post_url
#
# Therefore, we only need to bring post_content
# from the posts dataset.
post_context_df = posts_df[
    [
        "post_id",
        "suburb",
        "post_content"
    ]
].copy()


# Remove duplicate post records before merging.
post_context_df.drop_duplicates(
    subset=[
        "post_id",
        "suburb"
    ],
    inplace=True
)


# ============================================================
# MERGE POST CONTENT INTO COMMENTS
# ============================================================

# Attach the original post content to each comment.
#
# This gives each comment additional context
# for later relevance, aspect and sentiment analysis.
comments_df = comments_df.merge(
    post_context_df,

    on=[
        "post_id",
        "suburb"
    ],

    # Keep every comment even if a post
    # cannot be matched.
    how="left"
)


# ============================================================
# CHECK MERGE RESULT
# ============================================================

print(
    f"\nComments after merge: "
    f"{len(comments_df)}"
)


# Count how many comments could not
# find their original post content.
missing_context = (
    comments_df[
        "post_content"
    ]
    .isna()
    .sum()
)

print(
    f"Comments without post context: "
    f"{missing_context}"
)


# ============================================================
# CREATE CLEAN POST DATASET
# ============================================================

posts_clean = pd.DataFrame()


# --------------------------------------------
# BASIC INFORMATION
# --------------------------------------------

# Suburb associated with the Reddit post
posts_clean["suburb"] = (
    posts_df["suburb"]
)


# Identify the row as a post
posts_clean["source_type"] = "post"


# Original Reddit post ID
posts_clean["post_id"] = (
    posts_df["post_id"]
)


# Posts do not have a comment ID
posts_clean["comment_id"] = None


# --------------------------------------------
# TEXT
# --------------------------------------------

# Main text that will later be analysed
posts_clean["text"] = (
    posts_df[
        "post_content"
    ]
)


# Original Reddit post title
posts_clean["post_title"] = (
    posts_df[
        "post_title"
    ]
)


# For a post row, its own post content
# is also its context
posts_clean["post_context"] = (
    posts_df[
        "post_content"
    ]
)


# ============================================================
# POST DATE
# ============================================================

# Convert the post date into datetime format.
# Invalid dates will become NaT.
posts_clean["date_utc"] = pd.to_datetime(
    posts_df[
        "post_date_utc"
    ],
    errors="coerce",
    utc=True
)


# Extract year from the date
posts_clean["year"] = (
    posts_clean[
        "date_utc"
    ]
    .dt.year
)


# Extract month from the date
posts_clean["month"] = (
    posts_clean[
        "date_utc"
    ]
    .dt.month
)


# ============================================================
# POST ENGAGEMENT
# ============================================================

# Reddit post score
posts_clean["score"] = (
    posts_df[
        "post_score"
    ]
)


# ============================================================
# POST SUBREDDIT
# ============================================================

# Use the actual subreddit returned by Reddit
# if the column exists.
if "actual_subreddit" in posts_df.columns:

    posts_clean["subreddit"] = (
        posts_df[
            "actual_subreddit"
        ]
    )

else:

    posts_clean["subreddit"] = (
        posts_df[
            "searched_subreddit"
        ]
    )


# ============================================================
# EXPLICIT SUBURB MENTION
# ============================================================

# A post explicitly mentions the suburb if
# the suburb appears in either:
# - the title
# - the post content
posts_clean["explicit_suburb_mention"] = (

    posts_df[
        "keyword_in_title"
    ].fillna(False)

    |

    posts_df[
        "keyword_in_content"
    ].fillna(False)
)


# ============================================================
# POST RELATIONSHIP INFORMATION
# ============================================================

# Posts do not have a parent comment
posts_clean["parent_id"] = None


# Comment depth does not apply to posts
posts_clean["comment_depth"] = None


# ============================================================
# POST URL
# ============================================================

posts_clean["post_url"] = (
    posts_df[
        "post_url"
    ]
)


# Posts do not have comment URLs
posts_clean["comment_url"] = None


# ============================================================
# ANALYSIS COLUMNS
# ============================================================

# These columns are intentionally empty for now.
# They will be filled during later NLP analysis.
posts_clean["sentiment"] = None

posts_clean["sentiment_score"] = None

posts_clean["aspect"] = None

posts_clean["aspect_sentiment"] = None


# ============================================================
# CREATE CLEAN COMMENT DATASET
# ============================================================

comments_clean = pd.DataFrame()


# --------------------------------------------
# BASIC INFORMATION
# --------------------------------------------

# Suburb associated with the original search
comments_clean["suburb"] = (
    comments_df[
        "suburb"
    ]
)


# Identify the row as a comment
comments_clean["source_type"] = "comment"


# ID of the original Reddit post
comments_clean["post_id"] = (
    comments_df[
        "post_id"
    ]
)


# Unique Reddit comment ID
comments_clean["comment_id"] = (
    comments_df[
        "comment_id"
    ]
)


# ============================================================
# COMMENT TEXT
# ============================================================

# Main comment text that will
# later be analysed
comments_clean["text"] = (
    comments_df[
        "comment_content"
    ]
)


# Original parent post title
comments_clean["post_title"] = (
    comments_df[
        "post_title"
    ]
)


# Original parent post body.
# This came from the posts dataset during the merge.
comments_clean["post_context"] = (
    comments_df[
        "post_content"
    ]
)


# ============================================================
# COMMENT DATE
# ============================================================

comments_clean["date_utc"] = pd.to_datetime(
    comments_df[
        "comment_date_utc"
    ],
    errors="coerce",
    utc=True
)


# Extract year
comments_clean["year"] = (
    comments_clean[
        "date_utc"
    ]
    .dt.year
)


# Extract month
comments_clean["month"] = (
    comments_clean[
        "date_utc"
    ]
    .dt.month
)


# ============================================================
# COMMENT ENGAGEMENT
# ============================================================

# Reddit comment score
comments_clean["score"] = (
    comments_df[
        "comment_score"
    ]
)


# ============================================================
# COMMENT SUBREDDIT
# ============================================================

comments_clean["subreddit"] = (
    comments_df[
        "subreddit"
    ]
)


# ============================================================
# EXPLICIT SUBURB MENTION
# ============================================================

# Whether the suburb name appears
# directly in the comment text
comments_clean["explicit_suburb_mention"] = (
    comments_df[
        "contains_suburb"
    ]
)


# ============================================================
# COMMENT RELATIONSHIP INFORMATION
# ============================================================

# Parent post or parent comment ID
comments_clean["parent_id"] = (
    comments_df[
        "parent_id"
    ]
)


# Position of the comment
# within the reply tree
comments_clean["comment_depth"] = (
    comments_df[
        "comment_depth"
    ]
)


# ============================================================
# COMMENT URLS
# ============================================================

# URL of the parent post
comments_clean["post_url"] = (
    comments_df[
        "post_url"
    ]
)


# Direct URL to the Reddit comment
comments_clean["comment_url"] = (
    comments_df[
        "comment_url"
    ]
)


# ============================================================
# ANALYSIS COLUMNS
# ============================================================

# These are empty for now.
comments_clean["sentiment"] = None

comments_clean["sentiment_score"] = None

comments_clean["aspect"] = None

comments_clean["aspect_sentiment"] = None


# ============================================================
# COMBINE POSTS AND COMMENTS
# ============================================================

# Stack the standardised post rows
# and comment rows into one dataset.
master_df = pd.concat(
    [
        posts_clean,
        comments_clean
    ],
    ignore_index=True
)


# ============================================================
# REMOVE EXACT DUPLICATES
# ============================================================

# Remove rows that are completely duplicated.
master_df.drop_duplicates(
    inplace=True
)


# ============================================================
# SORT DATASET
# ============================================================

# Sort first by suburb,
# then by date.
master_df.sort_values(
    by=[
        "suburb",
        "date_utc",
        "source_type"
    ],
    inplace=True
)


# Reset row numbers after sorting.
master_df.reset_index(
    drop=True,
    inplace=True
)


# ============================================================
# FINAL COLUMN ORDER
# ============================================================

FINAL_COLUMNS = [
    "suburb",
    "source_type",
    "post_id",
    "comment_id",
    "text",
    "post_title",
    "post_context",
    "date_utc",
    "year",
    "month",
    "score",
    "subreddit",
    "explicit_suburb_mention",
    "parent_id",
    "comment_depth",
    "post_url",
    "comment_url",
    "sentiment",
    "sentiment_score",
    "aspect",
    "aspect_sentiment"
]


# Keep the columns in the desired order.
master_df = master_df[
    FINAL_COLUMNS
]


# ============================================================
# SAVE MASTER DATASET
# ============================================================

master_df.to_csv(
    OUTPUT_FILE,
    index=False
)


# ============================================================
# SUMMARY
# ============================================================

print("\n========================================")
print("MASTER DATASET CREATED")
print("========================================")


print(
    f"Post rows: "
    f"{len(posts_clean)}"
)


print(
    f"Comment rows: "
    f"{len(comments_clean)}"
)


print(
    f"Total rows: "
    f"{len(master_df)}"
)


# ============================================================
# SOURCE TYPE SUMMARY
# ============================================================

print("\nROWS BY SOURCE TYPE")
print("----------------------------------------")

print(
    master_df[
        "source_type"
    ].value_counts()
)


# ============================================================
# SUBURB SUMMARY
# ============================================================

print("\nROWS BY SUBURB")
print("----------------------------------------")

print(
    master_df
    .groupby(
        "suburb"
    )
    .size()
    .sort_values(
        ascending=False
    )
)


# ============================================================
# SUBREDDIT SUMMARY
# ============================================================

print("\nROWS BY SUBREDDIT")
print("----------------------------------------")

print(
    master_df
    .groupby(
        "subreddit"
    )
    .size()
    .sort_values(
        ascending=False
    )
)


# ============================================================
# MISSING TEXT CHECK
# ============================================================

missing_text = (
    master_df[
        "text"
    ]
    .isna()
    .sum()
)

print(
    f"\nRows with missing text: "
    f"{missing_text}"
)


# ============================================================
# MISSING POST CONTEXT CHECK
# ============================================================

missing_context = (
    master_df[
        "post_context"
    ]
    .isna()
    .sum()
)

print(
    f"Rows with missing post context: "
    f"{missing_context}"
)


# ============================================================
# FINAL FILE
# ============================================================

print(
    f"\nSaved to: "
    f"{OUTPUT_FILE}"
)


# ============================================================
# PREVIEW
# ============================================================

print("\nDATA PREVIEW")
print("----------------------------------------")

print(
    master_df[
        [
            "suburb",
            "source_type",
            "post_id",
            "comment_id",
            "text",
            "date_utc",
            "subreddit"
        ]
    ].head(20)
)