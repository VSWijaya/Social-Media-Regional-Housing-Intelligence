"""Basic sentiment scoring reconstructed from the original labelling notes.

This is not the original project script. It does not include the original
domain corrections, topic assignment, sampling, or review-flag rules.

Dependency: TextBlob (install with: pip install textblob).
"""

from textblob import TextBlob


def label_sentiment(text):
    """Return a TextBlob polarity score and its sentiment category.

    Scores range from -1 to +1. Scores of at least 0.05 are Positive,
    scores of at most -0.05 are Negative, and other scores are Neutral.
    """
    score = TextBlob(str(text)).sentiment.polarity

    if score >= 0.05:
        label = "Positive"
    elif score <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"

    return score, label
