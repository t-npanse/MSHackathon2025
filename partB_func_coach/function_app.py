import azure.functions as func
import datetime
import json
import logging
import utils

app = func.FunctionApp()

@app.route(route="analyze_transcript", auth_level=func.AuthLevel.ANONYMOUS)
def analyze_transcript(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    try:
        vtt_text = req.get_body().decode("utf-8")
    except Exception:
        return func.HttpResponse("Invalid request body", status_code=400)

    plain_text, duration = utils.strip_vtt(vtt_text)
    metrics = utils.transcript_metrics(plain_text, duration)

    return func.HttpResponse(
        json.dumps(metrics, indent=2),
        mimetype="application/json",
        status_code=200
    )

@app.function_name(name="sentiment_summary")
@app.route(route="sentiment_summary", auth_level=func.AuthLevel.ANONYMOUS)
def sentiment_summary(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("sentiment_summary triggered")

    try:
        text = req.get_body().decode("utf-8")
        if not text.strip():
            raise ValueError()
    except Exception:
        return func.HttpResponse("Request body must contain text.", status_code=400)

    scores = utils.sentiment_scores(text)

    return func.HttpResponse(
        json.dumps(scores, indent=2),
        mimetype="application/json",
        status_code=200
    )

