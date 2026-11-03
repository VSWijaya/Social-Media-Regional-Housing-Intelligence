import pandas as pd
import re
import time
from langdetect import detect, DetectorFactory
from transformers import AutoTokenizer

# =====================================================
# SETTINGS
# =====================================================

INPUT_FILE = "melbourne_suburb_stage1_clean.csv"
OUTPUT_FILE = "melbourne_suburb_stage2_audit.csv"

LANGUAGE_SAMPLE_SIZE = 10000

DetectorFactory.seed = 42


# =====================================================
# 1. LOAD DATA
# =====================================================

df = pd.read_csv(INPUT_FILE)

print(f"Rows loaded: {len(df):,}")


# =====================================================
# 2. FLAG SHORT TEXT
# =====================================================

df["word_count"] = (
    df["model_text"]
    .fillna("")
    .astype(str)
    .str.split()
    .str.len()
)

df["flag_short_text"] = df["word_count"] <= 5


# =====================================================
# 3. FLAG URL-ONLY TEXT
# =====================================================

url_only_pattern = re.compile(
    r"^\s*(URL|https?://\S+|www\.\S+)\s*[.!?]?\s*$",
    re.IGNORECASE
)

df["flag_url_only"] = (
    df["model_text"]
    .fillna("")
    .astype(str)
    .apply(
        lambda x: bool(url_only_pattern.match(x))
    )
)


# =====================================================
# 4. FLAG BOT / MODERATOR / SYSTEM MESSAGES
# =====================================================

system_patterns = [
    r"\bautomoderator\b",
    r"\bauto moderator\b",
    r"\bi am a bot\b",
    r"\bthis action was performed automatically\b",
    r"\bcontact the moderators\b",
    r"\bmessage the moderators\b",
    r"\bmoderator notice\b",
    r"\bsubmission has been removed\b",
    r"\bcomment has been removed\b"
]

system_regex = re.compile(
    "|".join(system_patterns),
    re.IGNORECASE
)

df["flag_bot_system"] = (
    df["model_text"]
    .fillna("")
    .astype(str)
    .apply(
        lambda x: bool(system_regex.search(x))
    )
)


# =====================================================
# 5. ALSO CHECK AUTHOR COLUMN FOR BOTS
# =====================================================

possible_author_columns = [
    "author",
    "username",
    "user",
    "comment_author",
    "post_author"
]

author_column = next(
    (
        col
        for col in possible_author_columns
        if col in df.columns
    ),
    None
)

if author_column:

    author_bot_mask = (
        df[author_column]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.contains(
            r"automoderator|auto.?moderator|bot$",
            regex=True
        )
    )

    df["flag_bot_system"] = (
        df["flag_bot_system"]
        | author_bot_mask
    )


# =====================================================
# 6. LANGUAGE DETECTION FUNCTION
# =====================================================

def detect_language(text):

    text = str(text).strip()

    # Very short text gives unreliable language results
    words = re.findall(r"[A-Za-z]+", text)

    if len(words) < 3:
        return "unknown"

    try:
        return detect(text)

    except:
        return "unknown"


# =====================================================
# 7. LANGUAGE AUDIT ON SAMPLE ONLY
# =====================================================

print("\nRunning language audit on sample...")

sample_size = min(
    LANGUAGE_SAMPLE_SIZE,
    len(df)
)

language_sample = df.sample(
    n=sample_size,
    random_state=42
).copy()

start_time = time.time()

language_sample["detected_language"] = (
    language_sample["model_text"]
    .fillna("")
    .astype(str)
    .apply(detect_language)
)

elapsed = time.time() - start_time

print(
    f"Language detection for "
    f"{sample_size:,} rows took "
    f"{elapsed:.1f} seconds."
)


# =====================================================
# 8. PRINT LANGUAGE RESULTS
# =====================================================

print("\nTop detected languages:")

print(
    language_sample[
        "detected_language"
    ]
    .value_counts()
    .head(15)
)


english_count = (
    language_sample[
        "detected_language"
    ]
    .eq("en")
    .sum()
)

known_language_count = (
    language_sample[
        "detected_language"
    ]
    .ne("unknown")
    .sum()
)

if known_language_count > 0:

    english_percentage = (
        english_count
        / known_language_count
        * 100
    )

    print(
        f"\nEnglish among detectable text: "
        f"{english_percentage:.2f}%"
    )


# Optional estimate for detecting all rows

estimated_full_minutes = (
    elapsed
    / sample_size
    * len(df)
    / 60
)

print(
    f"Estimated time for full "
    f"language detection: "
    f"{estimated_full_minutes:.1f} minutes"
)


# =====================================================
# 9. BERT TOKEN LENGTH
# =====================================================

print("\nLoading BERT tokenizer...")

tokenizer = AutoTokenizer.from_pretrained(
    "bert-base-uncased"
)

texts = (
    df["model_text"]
    .fillna("")
    .astype(str)
    .tolist()
)

token_lengths = []

batch_size = 5000

print("Calculating BERT token lengths...")

for start in range(
    0,
    len(texts),
    batch_size
):

    batch = texts[
        start:start + batch_size
    ]

    encoded = tokenizer(
        batch,
        add_special_tokens=True,
        truncation=False,
        padding=False
    )

    token_lengths.extend(
        len(tokens)
        for tokens
        in encoded["input_ids"]
    )


df["bert_token_count"] = token_lengths


# =====================================================
# 10. TOKEN LENGTH FLAGS
# =====================================================

df["over_64_tokens"] = (
    df["bert_token_count"] > 64
)

df["over_128_tokens"] = (
    df["bert_token_count"] > 128
)

df["over_256_tokens"] = (
    df["bert_token_count"] > 256
)


# =====================================================
# 11. REVIEW FLAG
# =====================================================

# We are NOT using language here yet because
# language was only checked on a sample.

df["needs_review"] = (
    df["flag_short_text"]
    | df["flag_url_only"]
    | df["flag_bot_system"]
)


# =====================================================
# 12. SAVE DATA
# =====================================================

df.to_csv(
    OUTPUT_FILE,
    index=False
)


# =====================================================
# 13. FINAL REPORT
# =====================================================

print("\n================================")
print("       STAGE 2 AUDIT REPORT")
print("================================")

print(
    f"Total rows:              "
    f"{len(df):,}"
)

print(
    f"Short text <= 5 words:   "
    f"{df['flag_short_text'].sum():,}"
)

print(
    f"URL-only:                "
    f"{df['flag_url_only'].sum():,}"
)

print(
    f"Bot/system:              "
    f"{df['flag_bot_system'].sum():,}"
)

print("\nBERT token lengths:")

print(
    f"> 64 tokens:             "
    f"{df['over_64_tokens'].sum():,}"
)

print(
    f"> 128 tokens:            "
    f"{df['over_128_tokens'].sum():,}"
)

print(
    f"> 256 tokens:            "
    f"{df['over_256_tokens'].sum():,}"
)

print(
    f"\nRows needing review:     "
    f"{df['needs_review'].sum():,}"
)

print(
    f"\nAudit file saved to:\n"
    f"{OUTPUT_FILE}"
)