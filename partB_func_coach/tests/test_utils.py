import utils

SAMPLE_VTT = """WEBVTT

00:00:00.000 --> 00:00:02.000
Hello everyone um welcome to the demo.

00:00:02.500 --> 00:00:04.000
We hope you enjoy it.
"""

def test_strip_and_metrics():
    plain, duration = utils.strip_vtt(SAMPLE_VTT)
    metrics = utils.transcript_metrics(plain, duration)

    assert "um" in plain.lower()
    assert metrics["word_count"] == 13
    assert metrics["filler"] == 1
    # duration ~1.5 sec so wpm ~ 520; allow small tolerance
    assert abs(metrics["wpm"] - 520) < 5
