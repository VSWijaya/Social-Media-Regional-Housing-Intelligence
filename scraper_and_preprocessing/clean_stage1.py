import pandas as pd
import numpy as np
import re
import html

# =========================
# 1. Load dataset
# =========================
INPUT_FILE = "melbourne_suburb_master_dataset.csv"
OUTPUT_FILE = "melbourne_suburb_stage1_clean.csv"
REMOVED_FILE = "melbourne_suburb_stage1_removed.csv"

df = pd.read_csv(INPUT_FILE)

print(f"Original rows: {len(df):,}")

removed_rows = []


# =========================
# 2. Remove exact duplicates
# =========================
duplicate_mask = df.duplicated(keep="first")

if duplicate_mask.any():
    duplicates = df.loc[duplicate_mask].copy()
    duplicates["removal_reason"] = "exact_duplicate"
    removed_rows.append(duplicates)

df = df.loc[~duplicate_mask].copy()


# =========================
# 3. Identify unusable text
# =========================
def is_unusable(value):
    if pd.isna(value):
        return True

    value = str(value).strip()

    return (
        value == ""
        or value.lower() in {"[deleted]", "[removed]"}
    )


# Remove comments that have no usable text
bad_comment_mask = (
    df["source_type"].eq("comment")
    & df["text"].apply(is_unusable)
)

bad_comments = df.loc[bad_comment_mask].copy()
bad_comments["removal_reason"] = "empty_or_deleted_comment"
removed_rows.append(bad_comments)

df = df.loc[~bad_comment_mask].copy()


# =========================
# 4. Basic text cleaning
# =========================
URL_PATTERN = re.compile(
    r"https?://\S+|www\.\S+",
    flags=re.IGNORECASE
)

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
WHITESPACE_PATTERN = re.compile(r"\s+")


def clean_text(value):

    if pd.isna(value):
        return ""

    value = str(value)

    # Convert things such as &amp; -> &
    value = html.unescape(value)

    # Remove HTML tags
    value = HTML_TAG_PATTERN.sub(" ", value)

    # Replace URLs instead of completely removing them
    value = URL_PATTERN.sub(" URL ", value)

    # Normalize spaces/newlines/tabs
    value = WHITESPACE_PATTERN.sub(" ", value)

    return value.strip()


# =========================
# 5. Create BERT model text
# =========================

# Clean post titles
titles = df["post_title"].apply(clean_text)


# Deleted post body is okay because we may still have the title
def clean_body(value):
    if is_unusable(value):
        return ""
    return clean_text(value)


bodies = df["text"].apply(clean_body)


# Posts: title + body
# Comments: comment text only
df["model_text"] = np.where(
    df["source_type"].eq("post"),
    (titles + " " + bodies).str.strip(),
    bodies
)


# =========================
# 6. Remove anything still empty
# =========================
empty_final_mask = df["model_text"].eq("")

empty_final = df.loc[empty_final_mask].copy()
empty_final["removal_reason"] = "empty_model_text"
removed_rows.append(empty_final)

df = df.loc[~empty_final_mask].copy()


# =========================
# 7. Save results
# =========================
df.to_csv(OUTPUT_FILE, index=False)

if removed_rows:
    removed_df = pd.concat(
        removed_rows,
        ignore_index=True
    )
    removed_df.to_csv(REMOVED_FILE, index=False)


# =========================
# 8. Cleaning report
# =========================
print("\n--- Stage 1 Cleaning Report ---")
print(f"Rows remaining: {len(df):,}")
print(f"Rows removed:   {sum(len(x) for x in removed_rows):,}")

print("\nSource types:")
print(df["source_type"].value_counts())

print(f"\nClean dataset saved to: {OUTPUT_FILE}")
print(f"Removed rows saved to: {REMOVED_FILE}")