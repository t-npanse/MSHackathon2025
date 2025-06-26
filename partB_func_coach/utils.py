import re
from typing import Dict, Tuple

FILLERS = re.compile(r'\b(um+|uh+|like|you know)\b', re.I)

def strip_vtt(vtt_text: str) -> Tuple[str, float]:
    """Return plain transcript text and total duration (in seconds)."""
    lines = []
    start_time = end_time = 0.0

    for line in vtt_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "-->" in line:          # a timestamp line
            start, end = line.split("-->")
            # convert 00:00:04.820 to seconds
            h1,m1,s1 = parse_ts(start)
            h2,m2,s2 = parse_ts(end)
            if start_time == 0.0:
                start_time = h1*3600 + m1*60 + s1
            end_time = h2*3600 + m2*60 + s2
        elif not line.isdigit():   # skip cue numbers
            lines.append(line)

    duration = max(0.1, end_time - start_time)
    return "\n".join(lines), duration

def parse_ts(ts: str) -> Tuple[int,int,float]:
    h, m, rest = ts.strip().split(":")
    return int(h), int(m), float(rest.replace(",", "."))

def transcript_metrics(text: str, duration_sec: float) -> Dict:
    words = text.split()
    word_count = len(words)
    wpm = round((word_count / duration_sec) * 60, 1)
    filler = len(FILLERS.findall(text))
    return {
        "word_count": word_count,
        "duration_sec": round(duration_sec, 1),
        "wpm": wpm,
        "filler": filler
    }


from azure.ai.textanalytics import TextAnalyticsClient
from azure.core.credentials import AzureKeyCredential
import os

def get_text_analytics_client() -> TextAnalyticsClient:
    endpoint = os.environ["COG_ENDPOINT"]
    key      = os.environ["COG_KEY"]
    return TextAnalyticsClient(endpoint, AzureKeyCredential(key))

def sentiment_scores(text: str) -> dict:
    """Return overall label and positive/negative percentages."""
    client = get_text_analytics_client()
    result = client.analyze_sentiment([text])[0]  # single doc
    overall = result.sentiment          # 'positive' | 'neutral' | 'negative' | 'mixed'
    pos = result.confidence_scores.positive
    neg = result.confidence_scores.negative
    return {
        "overall": overall,
        "positive_pct": round(pos, 2),
        "negative_pct": round(neg, 2)
    }
