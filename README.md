# Phase 1: Data Collection & Preprocessing

## Setup Instructions

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Reddit API
1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Select "script" type
4. Name it "SocialMediaHousingIntelligence"
5. Set redirect URI to `http://localhost:8080`
6. Copy the Client ID and Secret
7. Create `.env` file (copy from `.env.example`) and fill in your credentials

### 3. Run Data Collection
```bash
python run_collection.py
```

This will:
- Search r/melbourne for each of the 10 target suburbs
- Collect up to 500 posts per suburb (adjust in `config.py`)
- Collect top-level comments for each post
- Save raw data to `data/raw/`
- Clean, deduplicate, and classify topics
- Save processed data to `data/processed/`

### 4. Output Files
| File | Description |
|------|-------------|
| `data/raw/all_posts_raw.csv` | Raw collected posts |
| `data/raw/all_comments_raw.csv` | Raw collected comments |
| `data/processed/posts_processed.csv` | Cleaned posts with suburb/topic labels |
| `data/processed/comments_processed.csv` | Cleaned comments with suburb/topic labels |
| `data/processed/combined_for_analysis.csv` | Unified dataset ready for sentiment analysis |

### 5. Project Structure
```
.
├── config.py                 # Project configuration
├── reddit_collector.py       # Reddit API collection logic
├── data_preprocessor.py      # Cleaning & topic classification
├── run_collection.py         # Main pipeline runner
├── requirements.txt          # Python dependencies
├── .env.example            # Environment variable template
└── data/
    ├── raw/                  # Unprocessed Reddit data
    └── processed/            # Cleaned data for NLP phase
```

## Notes
- Reddit API has rate limits (~30 requests/minute). The script includes sleep delays.
- If data is insufficient for some suburbs, consider expanding to related subreddits (r/MelbourneSuburbs, r/AusFinance) or adjusting search queries.
- The suburb detection logic follows your proposal: comments mentioning non-target Melbourne suburbs are excluded to prevent misattribution.
