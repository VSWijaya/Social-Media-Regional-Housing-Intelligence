"""Main entry point for Phase 1: Data Collection & Preprocessing."""
import sys
from reddit_collector import RedditCollector
from data_preprocessor import run_preprocessing


def main():
    print("="*60)
    print("SOCIAL MEDIA REGIONAL HOUSING INTELLIGENCE")
    print("Phase 1: Data Collection & Preprocessing")
    print("="*60)

    # Step 1: Collect from Reddit
    print("\n[STEP 1] Collecting Reddit data...")
    collector = RedditCollector()
    posts_df, comments_df = collector.collect_all_data()

    # Step 2: Preprocess
    print("\n[STEP 2] Preprocessing data...")
    posts_clean, comments_clean = run_preprocessing()

    print("\n" + "="*60)
    print("Phase 1 Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Review data/processed/combined_for_analysis.csv")
    print("2. Move to Phase 2: Sentiment Analysis with VADER")
    print("3. Set up PostgreSQL database for storage")


if __name__ == "__main__":
    main()
