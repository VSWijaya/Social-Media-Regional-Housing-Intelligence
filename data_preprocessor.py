"""Data cleaning and preprocessing module."""
import re
import pandas as pd
import numpy as np
from config import (
    TARGET_SUBURBS, MELBOURNE_SUBURBS, TOPIC_KEYWORDS,
    RAW_DATA_DIR, PROCESSED_DATA_DIR
)


class DataPreprocessor:
    """Handles text cleaning, suburb detection, and topic classification."""

    def __init__(self):
        self.target_suburbs_lower = [s.lower() for s in TARGET_SUBURBS]
        self.melbourne_suburbs_lower = [s.lower() for s in MELBOURNE_SUBURBS]

    def clean_text(self, text):
        """
        Clean raw Reddit text:
        - Lowercase
        - Remove URLs
        - Remove special characters (keep basic punctuation)
        - Remove extra whitespace
        - Handle missing/deleted content
        """
        if pd.isna(text) or text in ["[deleted]", "[removed]", ""]:
            return ""

        text = str(text).lower()

        # Remove URLs
        text = re.sub(r'http\S+|www\.\S+', '', text)

        # Remove Reddit-specific formatting
        text = re.sub(r'\*\*|\*|__|_|#|>', '', text)

        # Remove special characters but keep letters, numbers, basic punctuation
        text = re.sub(r'[^a-zA-Z0-9\s.,!?\'-]', ' ', text)

        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()

        return text

    def detect_suburb(self, title, body, comments=None):
        """
        Detect which suburb a post/comment belongs to.
        Logic from your proposal (Section 4.4):
        1. Check title/body for target suburb
        2. If comment mentions another target suburb, assign there
        3. If mentions non-target Melbourne suburb, exclude
        4. Otherwise assign to main suburb
        """
        combined_text = f"{title} {body}".lower()

        # Find all target suburbs mentioned
        mentioned_targets = [
            suburb for suburb in self.target_suburbs_lower 
            if suburb in combined_text
        ]

        # Find non-target Melbourne suburbs
        mentioned_non_targets = [
            suburb for suburb in self.melbourne_suburbs_lower 
            if suburb not in self.target_suburbs_lower and suburb in combined_text
        ]

        if not mentioned_targets and mentioned_non_targets:
            return "EXCLUDE"  # Mentions other Melbourne suburb not in scope

        if not mentioned_targets:
            return "UNASSIGNED"

        # Return first mentioned target suburb (primary suburb)
        return mentioned_targets[0].title()

    def classify_topics(self, text):
        """
        Classify text into topic categories using keyword matching.
        Returns a list of matched topics (can be multiple).
        """
        text_lower = str(text).lower()
        matched_topics = []

        for topic, keywords in TOPIC_KEYWORDS.items():
            if any(keyword in text_lower for keyword in keywords):
                matched_topics.append(topic)

        return matched_topics if matched_topics else ["uncategorized"]

    def preprocess_posts(self, posts_df):
        """Apply full preprocessing pipeline to posts dataframe."""
        print(f"Preprocessing {len(posts_df)} posts...")

        df = posts_df.copy()

        # Clean text fields
        df["title_clean"] = df["title"].apply(self.clean_text)
        df["body_clean"] = df["body"].apply(self.clean_text)
        df["full_text"] = (df["title_clean"] + " " + df["body_clean"]).str.strip()

        # Remove duplicates
        df = df.drop_duplicates(subset=["post_id"])

        # Remove empty posts
        df = df[df["full_text"].str.len() > 10]

        # Detect suburb
        df["assigned_suburb"] = df.apply(
            lambda row: self.detect_suburb(row["title"], row["body"]), 
            axis=1
        )

        # Exclude posts about non-target suburbs
        df = df[df["assigned_suburb"] != "EXCLUDE"]

        # Classify topics
        df["topics"] = df["full_text"].apply(self.classify_topics)

        print(f"After preprocessing: {len(df)} valid posts")
        return df

    def preprocess_comments(self, comments_df, posts_df):
        """Apply preprocessing to comments with suburb assignment."""
        print(f"Preprocessing {len(comments_df)} comments...")

        df = comments_df.copy()

        # Clean text
        df["body_clean"] = df["body"].apply(self.clean_text)
        df = df[df["body_clean"].str.len() > 5]

        # Assign suburb from parent post
        post_suburb_map = posts_df.set_index("post_id")["assigned_suburb"].to_dict()
        df["assigned_suburb"] = df["post_id"].map(post_suburb_map)

        # Also check comment text for suburb mentions
        df["assigned_suburb"] = df.apply(
            lambda row: self._resolve_comment_suburb(row["body"], row["assigned_suburb"]),
            axis=1
        )

        df = df[df["assigned_suburb"] != "EXCLUDE"]
        df["topics"] = df["body_clean"].apply(self.classify_topics)

        print(f"After preprocessing: {len(df)} valid comments")
        return df

    def _resolve_comment_suburb(self, comment_body, parent_suburb):
        """Resolve suburb for a comment based on proposal logic."""
        body_lower = str(comment_body).lower()

        # Check if comment mentions another target suburb
        mentioned_targets = [
            s for s in self.target_suburbs_lower 
            if s in body_lower and s != str(parent_suburb).lower()
        ]

        if mentioned_targets:
            return mentioned_targets[0].title()

        # Check if mentions non-target Melbourne suburb
        mentioned_non_targets = [
            s for s in self.melbourne_suburbs_lower 
            if s not in self.target_suburbs_lower and s in body_lower
        ]

        if mentioned_non_targets and not mentioned_targets:
            return "EXCLUDE"

        return parent_suburb if parent_suburb else "UNASSIGNED"

    def save_processed(self, posts_df, comments_df):
        """Save processed data for next phase (NLP/Sentiment Analysis)."""
        posts_df.to_csv(f"{PROCESSED_DATA_DIR}/posts_processed.csv", index=False)
        comments_df.to_csv(f"{PROCESSED_DATA_DIR}/comments_processed.csv", index=False)

        # Create combined dataset for analysis
        posts_subset = posts_df[["post_id", "full_text", "assigned_suburb", "topics", "created_utc", "score"]].copy()
        posts_subset["type"] = "post"

        comments_subset = comments_df[["comment_id", "body_clean", "assigned_suburb", "topics", "created_utc", "score"]].copy()
        comments_subset = comments_subset.rename(columns={"comment_id": "post_id", "body_clean": "full_text"})
        comments_subset["type"] = "comment"

        combined = pd.concat([posts_subset, comments_subset], ignore_index=True)
        combined.to_csv(f"{PROCESSED_DATA_DIR}/combined_for_analysis.csv", index=False)

        print(f"\nProcessed data saved to: {PROCESSED_DATA_DIR}/")
        print(f"Combined records for analysis: {len(combined)}")


def run_preprocessing():
    """Run the full preprocessing pipeline."""
    preprocessor = DataPreprocessor()

    # Load raw data
    posts_df = pd.read_csv(f"{RAW_DATA_DIR}/all_posts_raw.csv")
    comments_df = pd.read_csv(f"{RAW_DATA_DIR}/all_comments_raw.csv")

    # Process
    posts_clean = preprocessor.preprocess_posts(posts_df)
    comments_clean = preprocessor.preprocess_comments(comments_df, posts_clean)

    # Save
    preprocessor.save_processed(posts_clean, comments_clean)

    return posts_clean, comments_clean


if __name__ == "__main__":
    run_preprocessing()
