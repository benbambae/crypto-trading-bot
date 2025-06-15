import pandas as pd
import os
from textblob import TextBlob

# Enhanced sentiment extractor with polarity score
def get_sentiment(text):
    try:
        return TextBlob(str(text)).sentiment.polarity  # Range: [-1, 1]
    except:
        return 0.0

# Process all DOGE_*.xlsx files
for filename in os.listdir():
    if filename.startswith('DOGE_') and filename.endswith('.xlsx'):
        try:
            df = pd.read_excel(filename)

            if 'text' in df.columns:
                df['sentiment'] = df['text'].apply(get_sentiment)
                df.to_excel(filename, index=False)
                print(f"Processed {filename}")
            else:
                print(f"'text' column not found in {filename}")
        except Exception as e:
            print(f"Failed {filename}: {e}")
