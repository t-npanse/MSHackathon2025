import utils

def test_sentiment_positive():
    text = "I absolutely love how clear this explanation is!"
    result = utils.sentiment_scores(text)
    assert result["overall"] in ("positive", "mixed")
    assert result["positive_pct"] > result["negative_pct"]
