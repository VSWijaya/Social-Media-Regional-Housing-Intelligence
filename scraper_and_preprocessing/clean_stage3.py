import pandas as pd

INPUT_FILE = "melbourne_suburb_stage2_audit.csv"
OUTPUT_FILE = "melbourne_suburb_stage2_clean.csv"

df = pd.read_csv(INPUT_FILE)

print(f"Before cleaning: {len(df):,}")

# Remove only obvious unusable content
remove_mask = (
    df["flag_bot_system"]
    | df["flag_url_only"]
)

removed = df[remove_mask].copy()
clean_df = df[~remove_mask].copy()

clean_df.to_csv(OUTPUT_FILE, index=False)

print(f"Removed: {len(removed):,}")
print(f"Remaining: {len(clean_df):,}")
print(f"Saved to: {OUTPUT_FILE}")