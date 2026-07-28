"""Project configuration for data collection."""
import os
from dotenv import load_dotenv

load_dotenv()

# Reddit API Credentials
REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT")

# Target suburbs for the dashboard
TARGET_SUBURBS = [
    "Collingwood", "Oakleigh", "Nunawading", "Eaglemont", "Richmond",
    "Carlton", "Vermont", "Dandenong", "Officer", "Clayton"
]

# Full Melbourne suburb list for exclusion/filtering
# (Load from a file or expand this list as needed)
MELBOURNE_SUBURBS = TARGET_SUBURBS + [
    "Melbourne", "Southbank", "Docklands", "Fitzroy", "Brunswick",
    "St Kilda", "Footscray", "Preston", "Glen Waverley", "Box Hill",
    "Doncaster", "Essendon", "Moonee Ponds", "Hawthorn", "Camberwell",
    "Malvern", "Caulfield", "Brighton", "Sandringham", "Frankston",
    "Springvale", "Noble Park", "Ringwood", "Wantirna", "Knox",
    "Boronia", "Ferntree Gully", "Rowville", "Mulgrave", "Wheelers Hill"
]

# Topic keywords for classification (from your proposal Table 7)
TOPIC_KEYWORDS = {
    "lifestyle_amenities": [
        "cafe", "restaurant", "park", "shopping", "supermarket", 
        "nightlife", "quiet", "convenient", "gym", "library", "pool",
        "beach", "trail", "walkable", "pub", "bar", "bakery"
    ],
    "education_employment": [
        "school", "university", "campus", "job", "work", "office",
        "employment", "career", "study", "degree", "kindergarten",
        "childcare", "commute", "train station", "bus"
    ],
    "crime_safety": [
        "safe", "unsafe", "crime", "theft", "robbery", "police",
        "dangerous", "security", "violence", "assault", "break-in",
        "burglary", "graffiti", "lighting", "street lights"
    ],
    "affordability": [
        "rent", "expensive", "cheap", "price", "cost", "affordable",
        "overpriced", "mortgage", "deposit", "budget", "housing",
        "property value", "market", "bargain", "deal"
    ]
}

# Data collection settings
MAX_POSTS_PER_SUBURB = 500  # Adjust based on API limits and needs
TIME_FILTER = "all"  # Options: all, year, month, week, day
SUBREDDIT = "melbourne"

# Output paths
RAW_DATA_DIR = "data/raw"
PROCESSED_DATA_DIR = "data/processed"
os.makedirs(RAW_DATA_DIR, exist_ok=True)
os.makedirs(PROCESSED_DATA_DIR, exist_ok=True)
