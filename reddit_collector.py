"""Reddit data collection module using PRAW."""
import praw
import pandas as pd
from datetime import datetime
import time
from config import (
    REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT,
    TARGET_SUBURBS, MELBOURNE_SUBURBS, MAX_POSTS_PER_SUBURB,
    TIME_FILTER, SUBREDDIT, RAW_DATA_DIR
)


class RedditCollector:
    """Handles Reddit API authentication and data collection."""

    def __init__(self):
        self.reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT
        )
        print(f"Authenticated as: {self.reddit.user.me()}")
        self.subreddit = self.reddit.subreddit(SUBREDDIT)

    def search_posts_for_suburb(self, suburb_name, limit=MAX_POSTS_PER_SUBURB):
        """
        Search r/melbourne for posts mentioning a specific suburb.
        Returns a list of post dictionaries.
        """
        posts = []
        query = f'"{suburb_name}"'

        print(f"Searching for: {suburb_name} (limit: {limit})")

        try:
            for submission in self.subreddit.search(
                query, 
                sort="relevance", 
                time_filter=TIME_FILTER,
                limit=limit
            ):
                post_data = {
                    "post_id": submission.id,
                    "title": submission.title,
                    "body": submission.selftext,
                    "author": str(submission.author) if submission.author else "[deleted]",
                    "created_utc": datetime.utcfromtimestamp(submission.created_utc),
                    "score": submission.score,
                    "num_comments": submission.num_comments,
                    "url": submission.url,
                    "permalink": f"https://reddit.com{submission.permalink}",
                    "subreddit": submission.subreddit.display_name,
                    "queried_suburb": suburb_name,
                    "collected_at": datetime.utcnow()
                }
                posts.append(post_data)

                # Rate limiting courtesy
                time.sleep(0.5)

        except Exception as e:
            print(f"Error searching for {suburb_name}: {e}")

        print(f"Found {len(posts)} posts for {suburb_name}")
        return posts

    def collect_comments_for_post(self, post_id, max_comments=100):
        """
        Collect top-level comments for a given post.
        Returns a list of comment dictionaries.
        """
        comments = []

        try:
            submission = self.reddit.submission(id=post_id)
            submission.comments.replace_more(limit=0)  # Skip "load more" comments

            for comment in submission.comments[:max_comments]:
                comment_data = {
                    "comment_id": comment.id,
                    "post_id": post_id,
                    "body": comment.body,
                    "author": str(comment.author) if comment.author else "[deleted]",
                    "created_utc": datetime.utcfromtimestamp(comment.created_utc),
                    "score": comment.score,
                    "permalink": f"https://reddit.com{comment.permalink}",
                    "collected_at": datetime.utcnow()
                }
                comments.append(comment_data)

        except Exception as e:
            print(f"Error collecting comments for post {post_id}: {e}")

        return comments

    def collect_all_data(self):
        """
        Main collection pipeline: collect posts and comments for all target suburbs.
        Saves raw data to CSV files.
        """
        all_posts = []
        all_comments = []

        for suburb in TARGET_SUBURBS:
            print(f"\n{'='*50}")
            print(f"Collecting data for: {suburb}")
            print(f"{'='*50}")

            # Collect posts
            posts = self.search_posts_for_suburb(suburb)
            all_posts.extend(posts)

            # Collect comments for each post
            for post in posts:
                comments = self.collect_comments_for_post(post["post_id"])
                all_comments.extend(comments)

            # Save incremental backup per suburb
            pd.DataFrame(posts).to_csv(
                f"{RAW_DATA_DIR}/posts_{suburb.lower()}.csv", 
                index=False
            )

        # Save combined dataset
        posts_df = pd.DataFrame(all_posts)
        comments_df = pd.DataFrame(all_comments)

        posts_df.to_csv(f"{RAW_DATA_DIR}/all_posts_raw.csv", index=False)
        comments_df.to_csv(f"{RAW_DATA_DIR}/all_comments_raw.csv", index=False)

        print(f"\n{'='*50}")
        print("Collection Complete!")
        print(f"Total posts: {len(posts_df)}")
        print(f"Total comments: {len(comments_df)}")
        print(f"Data saved to: {RAW_DATA_DIR}/")
        print(f"{'='*50}")

        return posts_df, comments_df


if __name__ == "__main__":
    collector = RedditCollector()
    posts_df, comments_df = collector.collect_all_data()
